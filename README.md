# windbg_auto_analysis

这只是一个安装mcp-windbg服务的脚本

需要自己手动安装 windbg，并配置符号表

需要自己手动安装 mcp-windbg
https://github.com/svnscha/mcp-windbg

这里的脚本就是把mcp-windbg 这个程序搞成一个后台服务而已

powershell 执行 install_mcp_windbg_service.ps1 即可

配置mcp

{
  "mcpServers": {
    "windbg": {
      "type": "http",
      "url": "http://ip:1203/mcp"
    }
  }
}