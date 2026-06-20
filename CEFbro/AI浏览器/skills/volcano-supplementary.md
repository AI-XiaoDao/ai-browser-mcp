# 火山社区/第三方模块补充技能书

> 涵盖 `火山系统API知识库\` 中 **尚未被其他技能书收录** 的全部社区第三方封装库。
> 共约 **170+ 模块**，按功能分类。

---

## 目录

- [一、MFC/WTL界面补充组件](#一mfcwtl界面补充组件)
- [二、UI框架（ECharts/IGR报表/XCGUI/MiniBlink/WebView2）](#二ui框架)
- [三、网络库补充](#三网络库补充)
- [四、COM对象封装](#四com对象封装)
- [五、数据库/存储补充](#五数据库存储补充)
- [六、第三方C/C++库封装](#六第三方cc库封装)
- [七、Lkuaiy系列库](#七lkuaiy系列库)
- [八、社区工具库（中文命名）](#八社区工具库)
- [九、STL标准模板封装](#九stl标准模板封装)
- [十、多媒体/音频](#十多媒体音频)
- [十一、其他w_*核心补充模块](#十一其他w_核心补充模块)

---

## 一、MFC/WTL界面补充组件

| 文件 | 包名 | 类/功能 |
|------|------|---------|
| w_mfc_adv_menu.wsv | 火山.MFC界面.超级菜单 | `超级菜单类` — 高级弹出菜单 |
| w_mfc_out_bar.wsv | 火山.MFC界面.卷帘式菜单 | `卷帘式菜单` — Outlook风格卷帘菜单; 常量: `卷帘菜单排列方式`, `卷帘菜单风格` |
| w_mfc_startup.wsv | 火山.MFC界面.基本 | MFC程序启动入口模板（无类，代码模板） |
| w_mfc_ui_cartoon_box.wsv | 火山.MFC界面.动画框 | `动画物体` — 动画播放组件 |
| w_wtl_adv_menu.wsv | 火山.WTL界面.超级菜单 | `超级菜单类` |
| w_wtl_control_ext1.wsv | 火山.WTL界面.扩展组件1 | `GIF动画框` |
| w_wtl_out_bar.wsv | 火山.WTL界面.卷帘式菜单 | `卷帘式菜单` |
| w_wtl_scintilla.wsv | 火山.视窗.窗口组件 | `火花代码编辑框` — Scintilla代码编辑器组件 |
| w_wtl_ui_cartoon_box.wsv | 火山.WTL界面.动画框 | `动画物体` |
| w_scintilla.wsv | 火山.视窗.窗口组件 | `火花代码编辑框`（MFC版） |

---

## 二、UI框架

### ECharts图表（6文件）

| 文件 | 包名 | 类/功能 |
|------|------|---------|
| mfc_ui_echarts_control.wsv | 火山.ECharts | `EC基础图表` — ECharts图表控件(MFC版) |
| wtl_ui_echarts_control.wsv | 火山.ECharts | `EC基础图表`（WTL版） |
| mfc_ui_echarts_const.wsv | 火山.ECharts | `坐标系类型`, `坐标轴类型`, `坐标轴刻度值计算方式` |
| mfc_ui_echarts_option.wsv | 火山.ECharts | `图表参数基础类` |
| mfc_ui_echarts_series.wsv | 火山.ECharts | `图表系列类` |
| mfc_ui_echarts_style.wsv | 火山.ECharts | `文本样式类` |

### IGR锐浪报表（8文件）

| 文件 | 包名 | 类/功能 |
|------|------|---------|
| w_IGRBasicObject.wsv | 火山.锐浪 | `IGR对象` — 报表基本对象 |
| w_IGRCollection.wsv | 火山.锐浪 | `部件框集合` |
| w_IGRCommonObject.wsv | 火山.锐浪 | `页眉`, `页脚`, `报表头`, `报表尾` |
| w_IGRComponent.wsv | 火山.锐浪 | `报表` — 主报表组件 |
| w_IGRConstant.wsv | 火山.锐浪 | `版本及日期`, `GR标识类`, `事件_报表` |
| w_IGREnhance.wsv | 火山.锐浪 | `GR辅助类`（MFC版） |
| w_wtl_IGREnhance.wsv | 火山.锐浪 | `GR辅助类`（WTL版） |
| w_IGRAuxiliaryTool.wsv | 火山.锐浪 | `二进制数据` |
| w_IGRExport.wsv | 火山.锐浪 | `导出选项` |

### XCGUI炫彩界面（8文件）

| 文件 | 包名 | 类/功能 |
|------|------|---------|
| xcgui.wsv | xc.gui | `xcbase`, `炫彩基类` — 炫彩界面基础 |
| xcgui_Browser.wsv | xc.gui | `炫彩MB浏览器` |
| xcgui_CEFBrowser.wsv | xc.gui | `炫彩CEF函数`, `炫彩CEFV8回调` |
| xcgui_adapter.wsv | xc.gui | `数据适配器` |
| xcgui_const.wsv | xc.gui | `元素类型` |
| xcgui_other.wsv | xc.gui | `guibase` |
| xcgui_struct.wsv | xc.gui | `单精度小数坐标数组类`, `坐标数组` |
| xcgui_xshape.wsv | xc.gui | `形状基类` |

### 浏览器组件

| 文件 | 包名 | 类/功能 |
|------|------|---------|
| mfc_ui_mb.wsv | 火山.MiniBlink浏览器组件 | `MB浏览器组件`（MFC版） |
| wtl_ui_mb.wsv | 火山.WTL.MiniBlink浏览器组件 | `MB浏览器组件`（WTL版） |
| vMiniBlink.wsv | 火山.MiniBlink浏览器 | `MB浏览器` — 独立Mini浏览器内核 |
| mfc_ui_webview2.wsv | 火山.Edge浏览框 | `Edge过滤类型`, `Edge按键种类`（MFC版） |
| wtl_ui_webview2.wsv | 火山.Edge浏览框 | 同上（WTL版） |
| mfc_ui_cef_browser.wsv | 火山.MFC界面.浏览器 | `CEF字节集类`（MFC版CEF） |
| wtl_ui_cef_browser.wsv | 火山.WTL界面.浏览器 | `CEF字节集类`（WTL版CEF） |

### 其他UI

| 文件 | 包名 | 类/功能 |
|------|------|---------|
| UI_Grid_Layout.wsv | 火山.原创软件 | `窗口组件数组`, `网格布局对齐方式类` |
| UiIni.wsv | 火山.原创软件 | `界面配置类f` — INI配置界面 |
| Exui.wsv | 火山.Exui | `Exui常量`, `ARGB色` |
| markdown.wsv | 火山.Markdown | `Markdown解析器` |

---

## 三、网络库补充

| 文件 | 包名 | 类/功能 |
|------|------|---------|
| HPSocket.wsv | 火山.原创软件 | `______客户端通用函数` — HP-Socket简化封装 |
| HPSocketSimple.wsv | 火山.原创软件 | `______HP套接字函数_模板`, `______客户端函数_模板` |
| HPWebsocket.wsv | 火山.原创软件 | `HPWebsocketClientFC` — HP-WebSocket封装 |
| WebSocket.wsv | FOFWEBSCOKET.com | `FOFWebsocket客户端` — 独立WebSocket客户端 |
| ixwebsocket.wsv | 火山.原创软件 | `网页套接字消息类型常量`, `网页套接字发送常量` — IXWebSocket库 |
| LibWebsockets.wsv | 火山.原创软件 | `WebSocketMsgType`, `WebSocketHttpHeader` — libwebsockets封装 |
| nanomsg.wsv | 火山.原创软件 | `进程通讯配置常量` — nanomsg消息队列 |
| kcp.wsv | 火山.原创软件 | `______KCP全局类` — KCP可靠UDP |
| libhv.wsv | 火山.原创软件 | 空模板 — libhv HTTP框架 |
| socket.wsv | 火山.原创软件 | `______异步套接字`, `______套接字` — 原始Socket封装 |
| curl.wsv | 火山.原创软件 | `______网页表单辅助` — curl简化封装 |
| TCPTable.wsv | 火山.原创软件 | `TCPTable类` — TCP连接表查询 |
| pocoUrl.wsv | 火山.程序 | `URL解析类F` — Poco URL解析 |
| LUrlParser.wsv | 火山.原创软件 | `URL解析类` |

---

## 四、COM对象封装

| 文件 | 包名 | 类/功能 |
|------|------|---------|
| COM_Base.wsv | 火山.原创软件 | COM基础宏定义 |
| COM_DebenuPDFLibrary.wsv | 火山.原创软件 | `DebenuPDF` — PDF操作 |
| COM_Dm.wsv | 火山.原创软件 | `大漠最后一个免费版` — 大漠插件 |
| COM_Scripting.wsv | 火山.原创软件 | `IDictionary` — Scripting.Dictionary |
| COM_WinHttp.wsv | 火山.原创软件 | `WinHttpFC` — WinHTTP请求 |
| COM_WshShell.wsv | 火山.原创软件 | `IWshCollection` — WshShell操作 |
| COM_msfeeds.wsv | 火山.程序 | `RSS操作类FC`, `IFeed` — RSS订阅 |
| COM_msscript.wsv | 火山.原创软件 | `IScriptControl` — MSScript脚本引擎 |
| COM_sapi.wsv | 火山.原创软件 | `ISpVoice` — SAPI语音合成 |

---

## 五、数据库/存储补充

| 文件 | 包名 | 类/功能 |
|------|------|---------|
| w_mysql.wsv | 火山.视窗.MYSQL数据库 | `Mysql数据库类`, `Mysql_SSL模式` — MySQL原生客户端 |
| leveldbTool.wsv | 火山.原创软件 | `______leveldb全局类` — LevelDB键值存储 |
| MMKV.wsv | 火山.原创软件 | MMKV简化封装 |
| MMKVMG.wsv | 火山.原创软件 | MMKV管理工具 |
| Mailslot.wsv | 火山.进程通讯 | `邮槽服务器` — 邮槽IPC |
| NamedPipe.wsv | 火山.进程通讯 | `命名管道` — 命名管道IPC |
| SimpleIni.wsv | 火山.原创软件 | `配置项_简易` — INI文件操作 |
| vol_dp1.wsv | 火山.数据操作支持2 | `数据操作支持类2`, `数据加密算法类型` |

---

## 六、第三方C/C++库封装

| 文件 | 包名 | 类/功能 |
|------|------|---------|
| Lua.wsv | 火山.原创软件 | `______lua基础函数` — Lua脚本引擎 |
| Poco.wsv | 火山.程序 | `强大网页套接字数据类型_常量类`, `强大网页套接字数据类` — Poco WebSocket |
| TesseractOcr.wsv | 火山.原创软件 | `TesseractOcr类` — OCR识别 |
| OpenCVSimple.wsv | 火山.原创软件 | `视频设备类型常量类` — OpenCV简化封装 |
| Jsoncpp.wsv | 火山.原创软件 | `键值对象模板` — jsoncpp封装 |
| Blat.wsv | 火山.原创软件 | `______Blat全局类` — 邮件发送 |
| BreakPad.wsv | 火山.原创软件 | `异常信息类` — 崩溃dump（社区版） |
| Cryptopp.wsv | 火山.原创软件 | `jsencrypt` — Crypto++ RSA/JS加密 |
| Detours.wsv | 火山.原创软件 | `HOOK类` — API Hook/Detours |
| G729A.wsv | 火山.原创软件 | `______电话音频编码_全局类` — G.729A音频编码 |
| GLog.wsv | 火山.原创软件 | `日志_全局类` — Google日志 |
| Hidapi.wsv | 火山.原创软件 | `HID设备枚举类` — HID USB设备 |
| LzmaSDK.wsv | 火山.原创软件 | `______LzmaSDK` — LZMA压缩 |
| OpensslTool.wsv | 火山.原创软件 | `______OpensslTool` — OpenSSL工具封装 |
| Pugixml.wsv | 火山.原创软件 | `pugi节点值` — pugixml XML解析 |
| PugixmlSimple.wsv | 火山.原创软件 | `xml格式常量` — pugixml简化 |
| Qrencode.wsv | 火山.原创软件 | `二维码类f` — 二维码生成 |
| Snappy.wsv | 火山.原创软件 | `压缩解压类_s` — Snappy压缩 |
| StormLib.wsv | 火山.原创软件 | `暴雪MPQ类`, `暴雪MPQ常量类` — MPQ文件操作 |
| Tars.wsv | 火山.程序 | `______QQTea` — QQ加密算法 |
| aria2.wsv | 火山.原创软件 | `下载器aria2类` — aria2下载引擎 |
| cppjieba.wsv | 火山.原创软件 | `结巴分词类` — 中文分词 |
| gumbo.wsv | 火山.原创软件 | `______网页解析模块` — Gumbo HTML解析（社区版） |
| kubazip.wsv | 火山.原创软件 | `酷包全局类` — ZIP操作封装 |
| libcpuid.wsv | 火山.原创软件 | `cpuid信息` — CPU信息检测 |
| libtcc.wsv | 火山.原创软件 | `______快脚本全局类` — TinyCC即时编译 |
| pdh.wsv | 火山.原创软件 | `性能计数器值_结构类` — Windows性能计数器 |
| taglib.wsv | 火山.原创软件 | `音频信息类` — 音频标签读取 |
| uchardet.wsv | 火山.原创软件 | `______网页编码检测_全局类` — 编码检测 |
| ZipUtils.wsv | 火山.程序 | `ZIP项目信息类F` — ZIP工具 |
| Zlib.wsv | 火山.原创软件 | `Zlib类` — Zlib压缩封装 |
| zlib类.wsv | 星火.zlib | `zlib` — 另一个Zlib封装 |
| aobscan.wsv | 火山.原创软件 | `字节集搜索类` — 特征码搜索 |

---

## 七、Lkuaiy系列库

| 文件 | 包名 | 类/功能 |
|------|------|---------|
| LkuaiyCode.wsv | LkuaiyHttp.com | `官方库基类_网络传输类`, `官方库基类_短信相关`, 多种哈希表 |
| LkuaiyCoding.wsv | LkuaiyHttp.com | `类_编码转换` |
| LkuaiyCurl.wsv | LkuaiyHttp.com | `类_CURL基类`, `微信支付_订单信息`, `微信支付_商户信息` |
| LkuaiyDebug.wsv | LkuaiyHttp.com | `类_利快云调试` |
| LkuaiyFunctional.wsv | LkuaiyHttp.com | `类_高速日志` |
| LkuaiyFunctionalNOMFC.wsv | LkuaiyHttp.com | `类_高速日志`（无MFC版） |
| LkuaiyJsoncpp.wsv | LkuaiyHttp.com | `高性能缓存表基础库`, `高性能缓存表事件` |
| LkuaiyLkuaiyHttp.wsv | LkuaiyHttp.com | `启动类`, `我的主窗口` |
| LkuaiyMultithreading.wsv | LkuaiyHttp.com | `线程_线程时钟` |
| LkuaiyMysql.wsv | 利快云.libmysql | `MYSQL连接选项` |
| LkuaiyQueue.wsv | LkuaiyHttp.com | `类_超级队列` |
| LkuaiySql.wsv | ODBC数据库.com | `ODBC数据库字段类` |
| Lkuaiypay.wsv | LkuaiyHttp.com | `类_微信支付` |
| Lkuaiytime.wsv | LkuaiyHttp.com | `类_时钟操作` |

---

## 八、社区工具库

### 文件/目录操作

| 文件 | 包名 | 类/功能 |
|------|------|---------|
| FileTool.wsv | 火山.原创软件 | `文件打开方式f`, `文件共享方式f` — 文件工具 |
| DirPathFile.wsv | 火山.原创软件 | `____目录文件操作类` — 目录遍历 |
| XWN_File.wsv | 火山.原创软件 | 文件操作（极小） |
| RC.wsv | 火山.原创软件 | `______资源操作` — 资源文件操作 |
| ShellLink.wsv | 火山.原创软件 | `______快捷方式` — 快捷方式创建 |
| Everything.wsv | 火山.原创软件 | `文件搜索类` — Everything搜索 |

### 系统/进程

| 文件 | 包名 | 类/功能 |
|------|------|---------|
| Process.wsv | 火山.原创软件 | `______进程操作辅助函数_全局类` |
| Kernel.wsv | 火山.原创软件 | `______位操作加强版` — 位运算 |
| Firewall.wsv | 火山.原创软件 | `防火墙类型_常量类`, `防火墙动作_常量类` |
| DeviceEnum.wsv | 火山.原创软件 | `__设备管理器测试类` — 设备枚举 |
| DiskidTool.wsv | 火山.原创软件 | `______硬件特征` — 硬盘序列号 |
| Rasapi.wsv | 火山.原创软件 | `宽带连接状态类` |
| pdh.wsv | 火山.原创软件 | `性能计数器值_结构类` |

### 编码/加密

| 文件 | 包名 | 类/功能 |
|------|------|---------|
| Encodec.wsv | 火山.原创软件 | `______编码转换辅助函数base64`, `代码页常量` |
| HashAlgorithm.wsv | 火山.原创软件 | `______校验算法` — 哈希计算 |
| RegisterAndKeygen.wsv | 火山.原创软件 | `生成授权类` — 授权码生成 |

### 文本/数据

| 文件 | 包名 | 类/功能 |
|------|------|---------|
| TextHelper.wsv | 火山.原创软件 | `______文本处理` |
| Chinese.wsv | 火山.原创软件 | `汉字字典更新_全局类` |
| CPPHelper.wsv | 火山.原创软件 | `const_char_point_array类` |
| Combination.wsv | 火山.原创软件 | `组合_不重复` — 排列组合 |
| math_exp_calc.wsv | 火山.数学公式计算 | `公式计算类` — 数学表达式计算 |
| Radom.wsv | 火山.原创软件 | `随机数类_不重复f` |
| vol_py_processor.wsv | 火山.拼音处理 | `拼音处理类` |

### 线程/定时

| 文件 | 包名 | 类/功能 |
|------|------|---------|
| Thread.wsv | 火山.原创软件 | `______线程辅助函数` |
| ThreadPool.wsv | 火山.原创软件 | `______线程池辅助函数` |
| ThreadPoolCPP.wsv | 火山.程序 | `标准线程池` |
| Event.wsv | 火山.原创软件 | `______信号` — 事件信号 |
| Timer.wsv | 火山.原创软件 | `时钟类_多媒体时钟` |
| TimerCounter.wsv | 火山.原创软件 | `计时器类F` |
| Croncpp.wsv | 火山.原创软件 | `时间表达式类` — Cron表达式 |
| DateTime.wsv | 火山.原创软件 | `______时间辅助函数`, `时间间隔常量` |

### 界面/窗口

| 文件 | 包名 | 类/功能 |
|------|------|---------|
| Menu.wsv | 火山.原创软件 | `______弹出菜单` |
| WindowHelper.wsv | 火山.原创软件 | `______CHM帮助文档_全局类` |
| KeyboardMouseSimulation.wsv | 火山.原创软件 | `键代码_常量类` |
| CaptureScreen.wsv | 火山.原创软件 | `______屏幕截图_全局类` |

### 网络/IP

| 文件 | 包名 | 类/功能 |
|------|------|---------|
| IPInfo.wsv | 火山.原创软件 | `纯真数据库类` — IP查询 |
| CompileLinkCommand.wsv | 火山.原创软件 | `编译命令_常用` |
| Base_Global_Macro_FC.wsv | 火山.原创软件 | `测试带构造函数的参考对象类` |

### 剪贴板/缓冲/配置

| 文件 | 包名 | 类/功能 |
|------|------|---------|
| Clipboard.wsv | 火山.原创软件 | `______剪辑版_全局类` |
| CBuffer.wsv | 火山.原创软件 | `缓冲区类` |
| Registry.wsv | 火山.原创软件 | `注册表根类型_常量类`, `注册表打开方式_常量类` |
| Console.wsv | 火山.原创软件 | `______控制台_全局类`, `控制台句柄常量`, `控制台文本颜色常量` |

### Office文档

| 文件 | 包名 | 类/功能 |
|------|------|---------|
| ExcelClassInterface.wsv | 火山.Excel2021支持库 | `Excel打开方式`, `Excel编码` — COM操作Excel |
| WordClassInterface.wsv | 火山.Word2021支持库 | `Word保存选项`, `Word保存格式`, `Word窗口状态` — COM操作Word |
| PowerPointClassInterface.wsv | 火山.PowrPoint2021支持库 | `PPT窗口状态`, `PPT幻灯片版式` — COM操作PPT |

### 正则/解析

| 文件 | 包名 | 类/功能 |
|------|------|---------|
| Deelx.wsv | 火山.原创软件 | `______正则辅助函数`, `匹配模式_常量类` |
| CustomSyntax.wsv | 火山.原创软件 | `______自定义循环` |

### 其他

| 文件 | 包名 | 类/功能 |
|------|------|---------|
| TreeStruct.wsv | 火山.原创软件 | `______树结构` — 社区版树结构 |
| w_SysHardwareInfo.wsv | 火山.系统操作支持库 | `鼠标按键类型`, `事件标志值` — 系统硬件信息 |

---

## 九、STL标准模板封装

| 文件 | 包名 | 类/功能 |
|------|------|---------|
| std_base.wsv | 火山.原创软件 | `_标准模板基础类` — STL模板基类 |
| std_vector.wsv | 火山.原创软件 | `组合模板` — std::vector |
| std_map.wsv | 火山.原创软件 | `map` — std::map |
| std_list.wsv | 火山.原创软件 | `双向链表迭代器模板` — std::list |
| std_deque.wsv | 火山.原创软件 | `双向队列模板` — std::deque |
| vector.wsv | 火山.原创软件 | `组合模板`, `vector` — 另一个vector封装 |
| iterator.wsv | 火山.原创软件 | 迭代器宏定义 |

---

## 十、多媒体/音频

| 文件 | 包名 | 类/功能 |
|------|------|---------|
| win_media_player.wsv | 火山.多媒体.播放器 | `媒体播放器` — WMP播放 |
| Wave.wsv | 火山.原创软件 | `音频播放f` |
| SoundTouch.wsv | 火山.音频处理 | `音频处理类` — 变调变速 |
| soundtouch2.wsv | 火山.原创软件 | `变声类` |
| WebRTCNS.wsv | 火山.原创软件 | `______音频降噪` — WebRTC降噪 |
| G729A.wsv | 火山.原创软件 | `______电话音频编码_全局类` |

---

## 十一、其他w_*核心补充模块

| 文件 | 包名 | 类/功能 |
|------|------|---------|
| w_AutoCAD2024.wsv | 火山.COM封装对象.AutoCAD | `AC窗口状态枚举`, `AC颜色枚举` — AutoCAD 2024版 |
| w_WinHTTP5_1.wsv | 火山.WinHTTP5_1 | `WinHttp选项` — WinHTTP 5.1封装 |
| w_mimolloc.wsv | 火山.视窗.内存扩展 | `高性能内存分配类` — mimalloc内存分配器 |
| w_pcomm.wsv | 火山.串口操作.PComm | `PCM波特率` — PComm串口库 |
| w_pdf_haru.wsv | 火山.视窗.PDF操作 | `PDF错误码` — Haru PDF生成库 |
| w_python.wsv | 火山.视窗.Python | `Py常量`, `Py异常类型` — Python集成（另一版） |
| w_qrencode.wsv | 火山.视窗.数据处理 | `二维码生成类` — 二维码（官方版） |
| w_taskbar_list.wsv | 火山.任务栏 | `任务栏进度状态`, `缩略图按钮掩码` — Win7+任务栏 |
| w_tts5_4.wsv | 火山.TTS语音引擎 | `TTS事件`, `TTS状态信息` — TTS 5.4语音引擎 |
| w_unrar.wsv | 火山.视窗.文件解压 | `RAR文件解压类` — RAR解压 |
| w_v8js.wsv | 火山.视窗.NodeJS | `JS平台类` — V8/NodeJS（另一版） |
| w_vol_rpc_service.wsv | 火山.网络.远程服务 | `远程服务端处理类` — RPC远程服务 |
| w_win_toast.wsv | 火山.视窗 | `视窗系统通知类` — Windows Toast通知 |
| w_yaml_cpp.wsv | 火山.基本 | `YAML输出样式`, `YAML节点类型` — YAML解析 |
| w_zlib.wsv | 火山.视窗.数据处理 | `压缩解压类` — zlib压缩（官方版） |
| w_zlib12.wsv | 火山.视窗.数据处理 | `压缩解压类` — zlib 1.2版 |
| w_Pugixml.wsv | 火山视窗.XML操作 | `XML节点值` — pugixml（官方版） |

---

## 快速查找索引（补充）

| 需要做什么 | 使用的模块/类 |
|-----------|-------------|
| MFC超级菜单 | w_mfc_adv_menu → `超级菜单类` |
| MFC卷帘菜单 | w_mfc_out_bar → `卷帘式菜单` |
| Scintilla代码编辑器 | w_scintilla / w_wtl_scintilla → `火花代码编辑框` |
| ECharts图表 | mfc_ui_echarts_control → `EC基础图表` |
| IGR锐浪报表 | w_IGRComponent → `报表` |
| XCGUI炫彩界面 | xcgui → `炫彩基类` |
| MiniBlink浏览器 | mfc_ui_mb / vMiniBlink → `MB浏览器组件` |
| WebView2/Edge | mfc_ui_webview2 → Edge浏览框 |
| MySQL数据库 | w_mysql → `Mysql数据库类` |
| WinHTTP请求 | w_WinHTTP5_1 / COM_WinHttp |
| WebSocket(多版本) | WebSocket / ixwebsocket / LibWebsockets / HPWebsocket |
| KCP可靠UDP | kcp → `______KCP全局类` |
| nanomsg消息队列 | nanomsg |
| libhv HTTP | libhv |
| LevelDB存储 | leveldbTool |
| 邮槽/命名管道IPC | Mailslot / NamedPipe |
| Lua脚本 | Lua |
| Poco框架 | Poco → WebSocket |
| Tesseract OCR | TesseractOcr |
| 结巴中文分词 | cppjieba |
| aria2下载 | aria2 |
| API Hook | Detours → `HOOK类` |
| 音频变调变速 | SoundTouch |
| 音频降噪 | WebRTCNS |
| G.729A音频编码 | G729A |
| Crypto++加密 | Cryptopp → `jsencrypt` |
| HID USB设备 | Hidapi |
| Everything搜索 | Everything |
| 屏幕截图 | CaptureScreen |
| 快捷方式 | ShellLink |
| Excel COM操作 | ExcelClassInterface |
| Word COM操作 | WordClassInterface |
| PPT COM操作 | PowerPointClassInterface |
| YAML解析 | w_yaml_cpp |
| pugixml XML | w_Pugixml / Pugixml |
| RAR解压 | w_unrar → `RAR文件解压类` |
| LZMA压缩 | LzmaSDK |
| Snappy压缩 | Snappy |
| MPQ文件 | StormLib |
| Windows Toast通知 | w_win_toast |
| 任务栏进度 | w_taskbar_list |
| mimalloc内存 | w_mimolloc |
| TTS 5.4语音 | w_tts5_4 |
| RPC远程服务 | w_vol_rpc_service |
| PDF生成(Haru) | w_pdf_haru |
| TinyCC即时编译 | libtcc |
| CPU信息 | libcpuid |
| 音频标签 | taglib |
| 编码检测 | uchardet |
| 数学公式计算 | math_exp_calc |
| Markdown解析 | markdown |
| STL vector/map/list | std_vector / std_map / std_list |
| 微信支付 | Lkuaiypay / LkuaiyCurl |
| 大漠插件 | COM_Dm |
| SAPI语音 | COM_sapi → `ISpVoice` |
| 标准线程池 | ThreadPoolCPP → `标准线程池` |
| INI配置 | SimpleIni |
| 排列组合 | Combination |

---

> 📘 **相关技能**：
> - [volcano-modules.md](volcano-modules.md) — 67核心模块API
> - [volcano-core-ext.md](volcano-core-ext.md) — 10核心扩展模块
> - [volcano-ext-libs.md](volcano-ext-libs.md) — 37扩展库模块
> - [yyjson-api.md](yyjson-api.md) — yyjson完整API
