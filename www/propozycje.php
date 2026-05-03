<?php
/**
 * Redirect legacy PL URL → unified /proposals?lang=pl
 */
header('Location: /proposals?lang=pl', true, 301);
exit;
