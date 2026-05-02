"""CQRS Command Handlers - Write side operations."""

from __future__ import annotations

import asyncio
import logging
import tempfile
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Coroutine

from redsl.api.cqrs.events import (
    event_store,
    ScanStarted,
    ScanProgress,
    ScanCompleted,
    ScanFailed,
    RefactorStarted,
    RefactorProgress,
    RefactorCompleted,
)
from redsl.api.cqrs.websocket_manager import ws_manager

logger = logging.getLogger(__name__)


# Command classes
@dataclass
class Command:
    """Base command."""
    command_id: str = ""
    correlation_id: str = ""  # For tracing across commands/events


@dataclass
class ScanRemoteCommand(Command):
    """Command to scan remote repository."""
    repo_url: str = ""
    branch: str = "main"
    depth: int = 1
    notify_ws: bool = True  # Send WebSocket updates


@dataclass
class RefactorCommand(Command):
    """Command to run refactoring cycle."""
    project_dir: str = ""
    dry_run: bool = True
    max_actions: int = 5
    llm_model: str | None = None
    notify_ws: bool = True


class CommandHandler(ABC):
    """Base command handler."""
    
    @abstractmethod
    async def handle(self, command: Command) -> dict[str, Any]:
        """Handle command, return result."""
        ...


class ScanRemoteHandler(CommandHandler):
    """Handler for ScanRemoteCommand."""
    
    async def handle(self, command: ScanRemoteCommand) -> dict[str, Any]:
        """Execute remote scan with event sourcing."""
        from redsl.analyzers import CodeAnalyzer
        from redsl.api.scan_routes import _clone_repo, _cleanup_repo, _validate_repo_url
        
        aggregate_id = f"scan:{command.repo_url}"
        
        # Emit started event
        started = ScanStarted(
            aggregate_id=aggregate_id,
            repo_url=command.repo_url,
            branch=command.branch,
            depth=command.depth,
        )
        await event_store.append(started)
        
        if command.notify_ws:
            await ws_manager.broadcast_event(started.to_dict())
        
        # Validate URL
        if not _validate_repo_url(command.repo_url):
            failed = ScanFailed(
                aggregate_id=aggregate_id,
                repo_url=command.repo_url,
                error_message="Invalid repository URL",
                error_type="validation_error",
            )
            await event_store.append(failed)
            if command.notify_ws:
                await ws_manager.broadcast_event(failed.to_dict())
            return {"status": "error", "detail": "Invalid repository URL"}
        
        # Progress: cloning
        progress_clone = ScanProgress(
            aggregate_id=aggregate_id,
            repo_url=command.repo_url,
            phase="clone",
            progress_percent=10,
            message="Cloning repository...",
        )
        await event_store.append(progress_clone)
        if command.notify_ws:
            await ws_manager.broadcast_event(progress_clone.to_dict())
        
        # Clone repository
        repo_path = await asyncio.to_thread(
            _clone_repo, command.repo_url, command.branch, command.depth
        )
        
        if repo_path is None:
            failed = ScanFailed(
                aggregate_id=aggregate_id,
                repo_url=command.repo_url,
                error_message="Failed to clone repository",
                error_type="clone_error",
            )
            await event_store.append(failed)
            if command.notify_ws:
                await ws_manager.broadcast_event(failed.to_dict())
            return {"status": "error", "detail": "Failed to clone repository"}
        
        try:
            # Progress: analyzing
            progress_analyze = ScanProgress(
                aggregate_id=aggregate_id,
                repo_url=command.repo_url,
                phase="analyze",
                progress_percent=50,
                message="Analyzing code...",
            )
            await event_store.append(progress_analyze)
            if command.notify_ws:
                await ws_manager.broadcast_event(progress_analyze.to_dict())
            
            # Analyze
            analyzer = CodeAnalyzer()
            analysis = await asyncio.to_thread(analyzer.analyze_project, repo_path)
            
            logger.info("ScanRemoteHandler: Analysis completed, alerts_count=%d", len(analysis.alerts))
            
            # Convert alerts to dicts
            alerts_list = [
                {
                    'type': a.get('type', 'unknown') if isinstance(a, dict) else getattr(a, 'type', 'unknown'),
                    'name': a.get('name', 'unknown') if isinstance(a, dict) else getattr(a, 'name', 'unknown'),
                    'severity': a.get('severity', 1) if isinstance(a, dict) else getattr(a, 'severity', 1),
                    'value': a.get('value', 0) if isinstance(a, dict) else getattr(a, 'value', 0),
                    'limit': a.get('limit', 10) if isinstance(a, dict) else getattr(a, 'limit', 10),
                    'message': a.get('message', '') if isinstance(a, dict) else getattr(a, 'message', ''),
                }
                for a in (analysis.alerts or [])
            ]
            
            # Extract top issues
            from redsl.api.scan_routes import _extract_top_issues, _generate_summary
            analysis_dict = {
                'total_files': getattr(analysis, 'total_files', 0),
                'total_lines': getattr(analysis, 'total_lines', 0),
                'avg_cc': getattr(analysis, 'avg_cc', 0),
                'critical_count': getattr(analysis, 'critical_count', 0),
                'alerts': alerts_list,
            }
            top_issues = _extract_top_issues(analysis_dict)
            summary = _generate_summary(analysis_dict)
            
            # Progress: complete
            progress_complete = ScanProgress(
                aggregate_id=aggregate_id,
                repo_url=command.repo_url,
                phase="complete",
                progress_percent=100,
                message="Analysis complete!",
            )
            await event_store.append(progress_complete)
            if command.notify_ws:
                logger.info("ScanRemoteHandler: Broadcasting complete progress event")
                await ws_manager.broadcast_event(progress_complete.to_dict())
            
            # Emit completed event
            completed = ScanCompleted(
                aggregate_id=aggregate_id,
                repo_url=command.repo_url,
                total_files=analysis_dict['total_files'],
                total_lines=analysis_dict['total_lines'],
                avg_cc=analysis_dict['avg_cc'],
                critical_count=analysis_dict['critical_count'],
                alerts=alerts_list,
                top_issues=top_issues,
                summary=summary,
            )
            await event_store.append(completed)
            if command.notify_ws:
                logger.info("ScanRemoteHandler: Broadcasting ScanCompleted event with %d alerts", len(alerts_list))
                await ws_manager.broadcast_event(completed.to_dict())
            
            return {
                "status": "success",
                "repo_url": command.repo_url,
                **analysis_dict,
                "top_issues": top_issues,
                "summary": summary,
            }
            
        except Exception as e:
            logger.exception("Analysis error")
            failed = ScanFailed(
                aggregate_id=aggregate_id,
                repo_url=command.repo_url,
                error_message=f"Analysis failed: {str(e)}",
                error_type="analysis_error",
            )
            await event_store.append(failed)
            if command.notify_ws:
                await ws_manager.broadcast_event(failed.to_dict())
            return {"status": "error", "detail": f"Analysis failed: {str(e)}"}
            
        finally:
            await asyncio.to_thread(_cleanup_repo, repo_path)


class RefactorHandler(CommandHandler):
    """Handler for RefactorCommand."""
    
    async def handle(self, command: RefactorCommand) -> dict[str, Any]:
        """Execute refactoring cycle with event sourcing."""
        from redsl.config import AgentConfig
        from redsl.orchestrator import RefactorOrchestrator
        from redsl.api.refactor_routes import _clear_project_history, _collect_modified_files
        
        aggregate_id = f"refactor:{command.project_dir}"
        project_path = Path(command.project_dir)
        
        # Emit started event
        started = RefactorStarted(
            aggregate_id=aggregate_id,
            project_dir=command.project_dir,
            dry_run=command.dry_run,
            max_actions=command.max_actions,
        )
        await event_store.append(started)
        
        if command.notify_ws:
            await ws_manager.broadcast_event(started.to_dict())
        
        try:
            # Progress: perceive
            progress = RefactorProgress(
                aggregate_id=aggregate_id,
                project_dir=command.project_dir,
                phase="perceive",
                current_action=0,
                total_actions=command.max_actions,
                message="Analyzing project...",
            )
            await event_store.append(progress)
            if command.notify_ws:
                await ws_manager.broadcast_event(progress.to_dict())
            
            # Configure and run
            config = AgentConfig.from_env()
            config.refactor.dry_run = command.dry_run
            if command.llm_model:
                config.llm.model = command.llm_model
            
            if command.dry_run:
                config.refactor.reflection_rounds = 0
            else:
                config.refactor.reflection_rounds = 1
            
            # Progress: decide/plan
            progress.phase = "decide"
            progress.message = "Evaluating DSL rules..."
            await event_store.append(progress)
            if command.notify_ws:
                await ws_manager.broadcast_event(progress.to_dict())
            
            orch = RefactorOrchestrator(config)
            
            # Progress: execute
            progress.phase = "execute"
            await event_store.append(progress)
            if command.notify_ws:
                await ws_manager.broadcast_event(progress.to_dict())
            
            report = await asyncio.to_thread(
                orch.run_cycle, project_path, max_actions=command.max_actions
            )
            
            files_modified = []
            if not command.dry_run:
                files_modified = await asyncio.to_thread(_collect_modified_files, project_path)
            
            # Progress: reflect
            progress.phase = "reflect"
            progress.message = "Generating report..."
            await event_store.append(progress)
            if command.notify_ws:
                await ws_manager.broadcast_event(progress.to_dict())
            
            # Emit completed event
            completed = RefactorCompleted(
                aggregate_id=aggregate_id,
                project_dir=command.project_dir,
                cycle_number=report.cycle_number,
                decisions_count=report.decisions_count,
                proposals_applied=report.proposals_applied,
                proposals_rejected=report.proposals_rejected,
                files_modified=files_modified,
            )
            await event_store.append(completed)
            if command.notify_ws:
                await ws_manager.broadcast_event(completed.to_dict())
            
            return {
                "status": "success",
                "cycle_number": report.cycle_number,
                "analysis_summary": report.analysis_summary,
                "decisions_count": report.decisions_count,
                "proposals_generated": report.proposals_generated,
                "proposals_applied": report.proposals_applied,
                "proposals_rejected": report.proposals_rejected,
                "files_modified": files_modified,
            }
            
        except Exception as e:
            logger.exception("Refactor error")
            # Emit failed event (would need RefactorFailed event class)
            return {"status": "error", "detail": str(e)}


class CommandBus:
    """Command Bus - dispatches commands to handlers."""
    
    def __init__(self) -> None:
        self._handlers: dict[type, CommandHandler] = {}
    
    def register(self, command_type: type, handler: CommandHandler) -> None:
        """Register handler for command type."""
        self._handlers[command_type] = handler
        logger.debug(f"Registered handler for {command_type.__name__}")
    
    async def dispatch(self, command: Command) -> dict[str, Any]:
        """Dispatch command to appropriate handler."""
        handler = self._handlers.get(type(command))
        if not handler:
            raise ValueError(f"No handler registered for {type(command).__name__}")
        
        logger.debug(f"Dispatching {type(command).__name__}")
        return await handler.handle(command)


# Global command bus
command_bus = CommandBus()

# Register handlers
command_bus.register(ScanRemoteCommand, ScanRemoteHandler())
command_bus.register(RefactorCommand, RefactorHandler())
