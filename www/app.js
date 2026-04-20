/* =============================================================
   REDSL Landing — Minimal JS
   No framework. Just progressive enhancement.
   ============================================================= */

(function () {
    'use strict';

    // ---------- Sticky masthead shadow on scroll ----------
    var masthead = document.querySelector('.masthead');
    if (masthead) {
        window.addEventListener('scroll', function () {
            masthead.classList.toggle('scrolled', window.scrollY > 8);
        }, { passive: true });
    }

    // ---------- Smooth scroll for in-page anchors ----------
    document.querySelectorAll('a[href^="#"]').forEach(function (a) {
        a.addEventListener('click', function (e) {
            var target = document.querySelector(a.getAttribute('href'));
            if (!target) return;
            e.preventDefault();
            target.scrollIntoView({ behavior: 'smooth', block: 'start' });
        });
    });

    // ---------- Contact form: live validation ----------
    var form = document.querySelector('.contact-form');
    if (form) {
        var emailField = form.querySelector('input[name="email"]');
        var nameField  = form.querySelector('input[name="name"]');
        var repoField  = form.querySelector('input[name="repo"]');
        var submitBtn  = form.querySelector('button[type="submit"]');

        function setInvalid(field, invalid) {
            if (!field) return;
            field.style.borderColor = invalid ? 'var(--red)' : '';
            field.setAttribute('aria-invalid', invalid ? 'true' : 'false');
        }

        function validEmail(value) {
            return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value);
        }

        function validRepo(value) {
            if (!value) return true;
            try { new URL(value); return true; } catch (_) { return false; }
        }

        if (emailField) {
            emailField.addEventListener('blur', function () {
                setInvalid(emailField, emailField.value !== '' && !validEmail(emailField.value));
            });
        }
        if (nameField) {
            nameField.addEventListener('blur', function () {
                setInvalid(nameField, nameField.value.trim() === '');
            });
        }
        if (repoField) {
            repoField.addEventListener('blur', function () {
                setInvalid(repoField, !validRepo(repoField.value.trim()));
            });
        }

        form.addEventListener('submit', function (e) {
            var errs = [];
            if (!nameField.value.trim()) { setInvalid(nameField, true); errs.push('name'); }
            if (!validEmail(emailField.value)) { setInvalid(emailField, true); errs.push('email'); }
            if (!validRepo(repoField.value.trim())) { setInvalid(repoField, true); errs.push('repo'); }
            if (errs.length) {
                e.preventDefault();
                (nameField && !nameField.value.trim() ? nameField : emailField).focus();
                return;
            }
            submitBtn.disabled = true;
            submitBtn.textContent = 'Wysyłam…';
        });
    }

    // ---------- Observer: reveal sections on scroll (CSS class-driven) ----------
    if ('IntersectionObserver' in window && !window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
        var io = new IntersectionObserver(function (entries) {
            entries.forEach(function (entry) {
                if (entry.isIntersecting) {
                    entry.target.classList.add('revealed');
                    io.unobserve(entry.target);
                }
            });
        }, { rootMargin: '0px 0px -60px 0px', threshold: 0.04 });

        document.querySelectorAll('.section').forEach(function (el) {
            el.classList.add('section-reveal');
            io.observe(el);
        });
    }

    // ---------- FAQ: close others on open (single accordion) ----------
    var details = document.querySelectorAll('.faq details');
    details.forEach(function (d) {
        d.addEventListener('toggle', function () {
            if (!d.open) return;
            details.forEach(function (other) {
                if (other !== d) other.removeAttribute('open');
            });
        });
    });

    // ---------- Auto-dismiss flash after 8s ----------
    var flash = document.querySelector('.flash');
    if (flash) {
        setTimeout(function () {
            flash.style.transition = 'opacity 0.5s ease, max-height 0.5s ease';
            flash.style.opacity = '0';
            flash.style.maxHeight = '0';
            setTimeout(function () { flash.remove(); }, 600);
        }, 8000);
    }

    // ---------- Subtle parallax on headline (desktop only) ----------
    if (window.matchMedia('(min-width: 900px)').matches &&
        !window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
        var headline = document.querySelector('.headline em');
        if (headline) {
            window.addEventListener('scroll', function () {
                var y = window.scrollY;
                if (y > 600) return;
                headline.style.transform = 'translateY(' + (y * 0.08) + 'px)';
            }, { passive: true });
        }
    }
})();
