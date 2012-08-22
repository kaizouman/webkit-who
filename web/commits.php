<?php
$now = date("Y");
$from = $_GET["from"];
if (($from=="") || !is_numeric($from) || ($from<2001) || ($from>$now)) 
    $from=$now;
$to = $_GET["to"];
if (($to=="") || !is_numeric($to) || ($to<$from) || ($to>$now))
    $to=$now;
$filter = $_GET["filter"];
if ($filter=="") $filter="company";
?>
<html>
<head>
<script type="text/javascript"
  src="dygraph-combined.js"></script>
<script type="text/javascript"
  src="webkit-who.js"></script>
</head>
<body>
<div id="graphdiv" style="width: 800px; height: 600px;"></div>
<p id="displaybar"><b>Display:</b></p>
<script type="text/javascript">
build_graph(<?=$from?>,<?=$to?>,"<?=$filter?>"); 
</script>
</body>
</html>
