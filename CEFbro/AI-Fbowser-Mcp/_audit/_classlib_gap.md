# 类库 API 面 → MCP 工具面 缺口报告

> 由 `_audit/classlib_gap.py` 生成。基准 = 技能书 `资料/类库/FBrowser浏览器` 全量方法。


- 类库方法(去重) = **533**（另排除基础设施类 827）
- 疑似已覆盖 = **170** (32%)
- **候选缺口 = 363**

## 候选缺口（按类聚合）


### 类_FBrowserVIP_控制器  (102)

`内核开关_禁用ConsoleAssert`  `内核开关_禁用ConsoleClear`  `内核开关_禁用ConsoleCount`  `内核开关_禁用ConsoleDebug`  `内核开关_禁用ConsoleDir`  `内核开关_禁用ConsoleError`  `内核开关_禁用ConsoleGroup`  `内核开关_禁用ConsoleInfo`  `内核开关_禁用ConsoleLog`  `内核开关_禁用ConsoleProfile`  `内核开关_禁用ConsoleTable`  `内核开关_禁用ConsoleTime`  `内核开关_禁用ConsoleTrace`  `内核开关_禁用ConsoleWarn`  `内核开关_禁用Debugger`  `内核开关_禁用Performance检测`  `内核开关_设置CSS内核`  `内核开关_设置EventIsTrusted`  `内核开关_设置V8内核`  `内核开关_设置Web内核`  `指纹_取调用计数`  `指纹_启用触摸事件`  `指纹_清空调用计数`  `指纹_虚拟AppCodeName`  `指纹_虚拟AppName`  `指纹_虚拟AppVersion`  `指纹_虚拟AudioInput设备`  `指纹_虚拟AudioOutput设备`  `指纹_虚拟Audio_定值`  `指纹_虚拟Audio_随机`  `指纹_虚拟BatteryManagerCharging`  `指纹_虚拟BatteryManagerChargingTime`  `指纹_虚拟BatteryManagerDischargingTime`  `指纹_虚拟BatteryManagerLevel`  `指纹_虚拟CSS字体指纹`  `指纹_虚拟Canvas_定值`  `指纹_虚拟Canvas_随机`  `指纹_虚拟Canvas字体指纹`  `指纹_虚拟CookieEnabled`  `指纹_虚拟Date时区`  `指纹_虚拟DeviceMemory`  `指纹_虚拟DevicePixelRatio`  `指纹_虚拟HardwareConcurrency`  `指纹_虚拟JavaEnabled`  `指纹_虚拟Languages`  `指纹_虚拟OnLine`  `指纹_虚拟Plugins`  `指纹_虚拟Product`  `指纹_虚拟ProductSub`  `指纹_虚拟Rect`  `指纹_虚拟UserAgent`  `指纹_虚拟Vendor`  `指纹_虚拟VendorSub`  `指纹_虚拟VideoInput设备`  `指纹_虚拟Viewport`  `指纹_虚拟WebGL_定值`  `指纹_虚拟WebGL_随机`  `指纹_虚拟Webdriver`  `指纹_虚拟Webglrenderer`  `指纹_虚拟Webglvendor`  `指纹_虚拟WebrtcIP`  `指纹_虚拟内核功能`  `指纹_虚拟定位`  `指纹_虚拟屏幕XY`  `指纹_虚拟屏幕colorDepth`  `指纹_虚拟屏幕pixelDepth`  `指纹_虚拟屏幕分辨率`  `指纹_虚拟屏幕可用高度和宽度`  `指纹_虚拟屏幕方向`  `指纹_设置SSL加密套件`  `清理数据`  `逐字分割`  `高级_创建标签浏览器`  `高级_发送触摸事件`  `高级_发送键盘事件`  `高级_发送鼠标事件`  `高级_取当前环境ID清单`  `高级_启用执行环境`  `高级_执行JS`  `高级_执行JS_主框架`  `高级_执行JS_全部框架`  `高级_执行JS_框架ID`  `高级_执行JS_框架序号`  `高级_清空代理`  `高级_网页截图`  `高级_设置代理`  `高级_设置触发鼠标触摸事件`  `高级触摸_单击`  `高级触摸_取消`  `高级触摸_按下`  `高级触摸_放开`  `高级触摸_移动`  `高级键盘_单击`  `高级键盘_按下`  `高级键盘_放开`  `高级键盘_输入字符`  `高级键盘_输入文本`  `高级鼠标_单击`  `高级鼠标_按下`  `高级鼠标_放开`  `高级鼠标_滚轮滚动`  `高级鼠标_移动`

### 类_FBrowser_应用事件  (27)

`即将处理命令行`  `执行关闭完毕`  `扩展插件_创建失败`  `扩展插件_创建成功`  `扩展插件_卸载成功`  `扩展插件_载入成功`  `注册自定义方案`  `渲染_VIP_WebSocket客户端_关闭`  `渲染_VIP_WebSocket客户端_创建`  `渲染_VIP_WebSocket客户端_发送数据`  `渲染_VIP_WebSocket客户端_接收数据`  `渲染_VIP_WebSocket客户端_连接服务器`  `渲染_即将创建V8环境`  `渲染_即将初始化WebKit`  `渲染_即将捕获异常`  `渲染_即将释放V8环境`  `渲染_即将销毁浏览器`  `渲染_收到消息`  `渲染_浏览器创建`  `渲染_焦点节点改变`  `渲染_载入开始`  `渲染_载入状态被改变`  `渲染_载入结束`  `渲染_载入错误`  `类_初始化`  `类_清理`  `获取默认事件`

### FBrowser初始化控制  (20)

`FBrowser_JS交互_删除`  `FBrowser_JS交互_注册`  `FBrowser_关闭`  `FBrowser_内存_压缩清理`  `FBrowser_创建URL请求`  `FBrowser_初始化`  `FBrowser_初始化_设置V8环境默认堆栈大小`  `FBrowser_初始化_设置内存释放`  `FBrowser_初始化_设置守护`  `FBrowser_取初始化缓存目录`  `FBrowser_取版本号`  `FBrowser_消息循环_执行`  `FBrowser_消息循环_设置系统模式`  `FBrowser_消息循环_运行`  `FBrowser_消息循环_退出`  `FBrowser_自定义方案_注册`  `FBrowser_自定义方案_清理`  `FBrowser_设置程序DPI模式`  `FBrowser_进程_取当前进程类型`  `启用自带调试提示`

### FBrowser辅助功能  (18)

`FBrowser_Parser_Base64编码`  `FBrowser_Parser_Base64解码`  `FBrowser_Parser_URI编码`  `FBrowser_Parser_URI解码`  `FBrowser_Parser_写入JSON`  `FBrowser_Parser_取数据URI`  `FBrowser_Parser_字节值解析为JSON`  `FBrowser_Parser_解析JSON`  `FBrowser_启用异常收集`  `FBrowser_浏览器_取ID清单`  `FBrowser_浏览器_取数量`  `FBrowser_浏览器_取用户标识清单`  `FBrowser_浏览器_通过ID取浏览器`  `FBrowser_浏览器_通过序号取浏览器`  `FBrowser_浏览器_通过用户标识取浏览器`  `FBrowser_浏览器_通过窗口句柄取浏览器`  `FBrowser_清理全局缓存`  `异常收集回调模板函数`

### 类_FBrowser_V8值  (16)

`FBrowser_V8值_创建函数`  `FBrowser_V8值_创建双精度小数型值`  `FBrowser_V8值_创建数组值`  `FBrowser_V8值_创建数组缓存值`  `FBrowser_V8值_创建整型值`  `FBrowser_V8值_创建文本值`  `FBrowser_V8值_创建无符号整型值`  `FBrowser_V8值_创建日期值`  `FBrowser_V8值_创建未定义类`  `FBrowser_V8值_创建空类`  `FBrowser_V8值_创建类`  `FBrowser_V8值_创建逻辑值`  `将重新抛出异常`  `执行函数`  `清理异常`  `调整外部内存大小`

### 类_FBrowser_浏览器  (15)

`FBrowser_创建后台浏览器`  `FBrowser_创建后台浏览器_同步`  `FBrowser_创建浏览器`  `FBrowser_创建浏览器_同步`  `停止载入`  `可否前进`  `尝试关闭浏览器`  `开始下载`  `打开对话框`  `显示隐藏窗口`  `清理缓存`  `移动窗口`  `设置代理`  `重新载入`  `重新载入_忽略缓存`

### 类_FBrowser_命令行  (15)

`FBrowser_命令行_创建`  `FBrowser_命令行_取全局`  `启用单进程模式`  `启用录音`  `启用摄像头`  `启用无头模式`  `启用自动播放`  `启用跨框架操作模式`  `忽略GPU禁用清单`  `插入值`  `禁用GPU`  `禁用GPU缓存`  `禁用代理`  `设置全局代理`  `设置远程调试端口`

### 类_FBrowser_菜单模式  (13)

`存在快捷键`  `存在快捷键_索引`  `添加Check菜单`  `添加Radio菜单`  `添加分隔栏`  `添加子菜单`  `添加菜单`  `移除快捷键`  `移除快捷键_索引`  `设置快捷键`  `设置快捷键_索引`  `选中状态`  `选中状态_索引`

### 类_FBrowser_服务器事件  (8)

`收到HTTP请求`  `收到WebSocket消息`  `收到WebSocket请求`  `收到WebSocket连接`  `收到客户端断开连接`  `收到客户端连接`  `类_初始化`  `类_清理`

### FBrowserVIP全局功能  (8)

`FBrowser_VIP功能_启用插件高级功能`  `FBrowser_VIP过滤器_修改内容`  `FBrowser_VIP过滤器_取消修改内容`  `FBrowser_VIP过滤器_取消全部修改内容`  `FBrowser_VIP过滤器_取消全部替换资源`  `FBrowser_VIP过滤器_取消替换资源`  `FBrowser_VIP过滤器_替换资源_数据`  `FBrowser_VIP过滤器_替换资源_文件`

### 类_FBrowser_URL请求事件  (7)

`上传进度`  `即将完成`  `开始创建`  `类_初始化`  `类_清理`  `获取到数据`  `读取结束`

### 类_FBrowser_任务运行器  (7)

`FBrowser_任务运行器_取当前`  `FBrowser_任务运行器_取指定线程`  `FBrowser_任务运行器_投递任务`  `FBrowser_任务运行器_投递任务_延迟`  `FBrowser_任务运行器_是否指定线程上调用`  `投递任务`  `投递延时任务`

### 类_FBrowser_V8拦截器  (6)

`类_初始化`  `类_清理`  `获取_名`  `获取_索引`  `设置_名`  `设置_索引`

### FBrowser类辅助  (5)

`FBrowser创建类指针`  `FBrowser取执行类`  `FBrowser设置类`  `FBrowser释放当前类`  `FBrowser释放类`

### 类_FBrowserVIP_开发者DOM  (5)

`枚举DOM`  `清除查找`  `移除节点`  `移除节点属性`  `预查找文本`

### 类_FBrowserVIP_通用回调  (4)

`列表数据回调`  `数据回调`  `类_初始化`  `类_清理`

### 类_FBrowser_JS交互事件  (4)

`即将取消查询`  `即将查询`  `类_初始化`  `类_清理`

### 类_FBrowser_资源过滤器  (4)

`修改数据`  `类_初始化`  `类_清理`  `获取数据`

### 类_FBrowser_下载图片回调  (3)

`图片下载完成`  `类_初始化`  `类_清理`

### 类_FBrowser_打开文件对话框回调  (3)

`即将关闭文件对话框`  `类_初始化`  `类_清理`

### 类_FBrowser_打印为PDF回调  (3)

`即将完成打印`  `类_初始化`  `类_清理`

### FBrowser_双文本数组  (3)

`到下一个`  `到数组首`  `查找数据`

### FBrowser_文本数组  (3)

`到下一个`  `到数组首`  `到火山文本数组`

### 类_FBrowser_框架  (3)

`访问DOM对象`  `载入地址`  `载入请求`

### 类_FBrowser_请求  (3)

`获取地址_首件cookie`  `设置地址_首件cookie`  `设置标识`

### 类_FBrowser_POST数据  (3)

`增加元素`  `移除元素`  `移除所有元素`

### 类_FBrowser_V8环境  (3)

`FBrowser_V8_注册JS扩展`  `FBrowser_V8环境_取当前环境`  `FBrowser_V8环境_取运行环境`

### 类_FBrowser_同步辅助类  (3)

`停止等待`  `添加字节集`  `清理数据`

### 类_FBrowser_值转换  (3)

`FBrowser_字节集到字节集`  `FBrowser_数据到字节集`  `FBrowser_文本到字节集`

### 类_FBrowser_字符串回调  (2)

`类_初始化`  `类_清理`

### 类_FBrowser_JS回调  (2)

`类_初始化`  `类_清理`

### 类_FBrowser_DOM回调  (2)

`类_初始化`  `类_清理`

### 类_FBrowser_任务回调  (2)

`类_初始化`  `类_清理`

### 类_FBrowser_Cookie回调  (2)

`类_初始化`  `类_清理`

### 类_FBrowser_V8处理程序  (2)

`类_初始化`  `类_清理`

### 类_FBrowser_V8存取器  (2)

`类_初始化`  `类_清理`

### 类_FBrowser_清理缓存回调  (2)

`类_初始化`  `类_清理`

### FBrowser_矩形位置数组  (2)

`到下一个`  `到数组首`

### FBrowser_拖拽位置数组  (2)

`到下一个`  `到数组首`

### FBrowser_下划线组成数组  (2)

`到下一个`  `到数组首`

### 类_FBrowser_浏览器事件  (2)

`类_初始化`  `类_清理`

### 类_FBrowser_资源处理器  (2)

`类_初始化`  `类_清理`

### 类_FBrowser_开发者消息事件  (2)

`类_初始化`  `类_清理`

### 类_FBrowser_Cookie管理器  (2)

`FBrowser_Cookie管理器_取全局`  `刷新Cookie`

### 类_FBrowser_服务器  (2)

`FBrowser_服务器_创建`  `关闭连接`

### 类_FBrowser_读取流  (2)

`FBrowser_读取流_从数据创建`  `FBrowser_读取流_从文件创建`

### 类_FBrowser_字节集数组  (2)

`到下一个`  `到数组首`

### 类_FBrowser_POST元素数组  (2)

`到下一个`  `到数组首`

### 类_FBrowser_X509证书数组  (2)

`到下一个`  `到数组首`

### 类_FBrowser_V8值数组  (2)

`到下一个`  `到数组首`

### 类_FBrowser_事件智能指针  (1)

`FBrowser创建事件智能指针`

### 类_FBrowser_请求环境  (1)

`FBrowser_请求环境_取全局`

### 类_FBrowser_方案注册  (1)

`添加自定义方案`

### 类_FBrowser_拖拽数据  (1)

`增加文件`


## 疑似已覆盖（抽样 200）

- FBrowser_文本 :: 设置值
- 类_FBrowser_应用事件 :: 请求环境初始化完毕
- 类_FBrowser_应用事件 :: 浏览器_初始化完毕
- 类_FBrowser_应用事件 :: 浏览器_即将启动子进程
- 类_FBrowser_应用事件 :: 浏览器_即将启动消息调度
- 类_FBrowser_应用事件 :: 进程间消息_收到主进程消息
- 类_FBrowser_浏览器事件 :: 浏览器_收到消息
- 类_FBrowser_浏览器事件 :: 浏览器_即将导航
- 类_FBrowser_浏览器事件 :: 浏览器_从标签打开地址
- 类_FBrowser_浏览器事件 :: 浏览器_请求证书错误
- 类_FBrowser_浏览器事件 :: 浏览器_选择客户端证书
- 类_FBrowser_浏览器事件 :: 浏览器_渲染视图
- 类_FBrowser_浏览器事件 :: 浏览器_渲染意外终止
- 类_FBrowser_浏览器事件 :: 浏览器_获得需授权证书
- 类_FBrowser_浏览器事件 :: 浏览器_创建完毕
- 类_FBrowser_浏览器事件 :: 浏览器_即将打开新窗口
- 类_FBrowser_浏览器事件 :: 浏览器_打开新窗口失败
- 类_FBrowser_浏览器事件 :: 浏览器_即将打开开发者窗口
- 类_FBrowser_浏览器事件 :: 浏览器_执行关闭
- 类_FBrowser_浏览器事件 :: 浏览器_即将关闭
- 类_FBrowser_浏览器事件 :: 浏览器_地址被改变
- 类_FBrowser_浏览器事件 :: 浏览器_标题被改变
- 类_FBrowser_浏览器事件 :: 浏览器_网页图标被改变
- 类_FBrowser_浏览器事件 :: 浏览器_全屏模式被改变
- 类_FBrowser_浏览器事件 :: 浏览器_工具栏被改变
- 类_FBrowser_浏览器事件 :: 浏览器_状态栏被改变
- 类_FBrowser_浏览器事件 :: 浏览器_控制台消息
- 类_FBrowser_浏览器事件 :: 浏览器_自动调整尺寸
- 类_FBrowser_浏览器事件 :: 浏览器_加载进度被改变
- 类_FBrowser_浏览器事件 :: 浏览器_光标被改变
- 类_FBrowser_浏览器事件 :: 浏览器_即将改变媒体访问
- 类_FBrowser_浏览器事件 :: 浏览器_即将加载资源
- 类_FBrowser_浏览器事件 :: 浏览器_获取资源处理器
- 类_FBrowser_浏览器事件 :: 浏览器_重定向资源
- 类_FBrowser_浏览器事件 :: 浏览器_响应资源
- 类_FBrowser_浏览器事件 :: 浏览器_获取资源过滤器
- 类_FBrowser_浏览器事件 :: 浏览器_资源加载完毕
- 类_FBrowser_浏览器事件 :: 浏览器_处理协议请求
- 类_FBrowser_浏览器事件 :: 浏览器_载入状态被改变
- 类_FBrowser_浏览器事件 :: 浏览器_载入开始
- 类_FBrowser_浏览器事件 :: 浏览器_载入结束
- 类_FBrowser_浏览器事件 :: 浏览器_载入错误
- 类_FBrowser_浏览器事件 :: 浏览器_即将打开菜单
- 类_FBrowser_浏览器事件 :: 浏览器_菜单被调用
- 类_FBrowser_浏览器事件 :: 浏览器_菜单被点击
- 类_FBrowser_浏览器事件 :: 浏览器_菜单被关闭
- 类_FBrowser_浏览器事件 :: 浏览器_即将运行快捷菜单
- 类_FBrowser_浏览器事件 :: 浏览器_即将运行快捷菜单命令
- 类_FBrowser_浏览器事件 :: 浏览器_即将取消快捷菜单
- 类_FBrowser_浏览器事件 :: 浏览器_可下载
- 类_FBrowser_浏览器事件 :: 浏览器_即将下载
- 类_FBrowser_浏览器事件 :: 浏览器_正在下载
- 类_FBrowser_浏览器事件 :: 浏览器_按下某键
- 类_FBrowser_浏览器事件 :: 浏览器_按下某键后
- 类_FBrowser_浏览器事件 :: 浏览器_即将打开对话框
- 类_FBrowser_浏览器事件 :: 浏览器_JS即将打开对话框
- 类_FBrowser_浏览器事件 :: 浏览器_JS即将打开离开对话框
- 类_FBrowser_浏览器事件 :: 浏览器_JS重置对话框
- 类_FBrowser_浏览器事件 :: 浏览器_JS对话框关闭
- 类_FBrowser_浏览器事件 :: 浏览器_即将失去焦点
- 类_FBrowser_浏览器事件 :: 浏览器_请求焦点
- 类_FBrowser_浏览器事件 :: 浏览器_收到焦点
- 类_FBrowser_浏览器事件 :: 浏览器_查找返馈
- 类_FBrowser_浏览器事件 :: 浏览器_拖拽进入
- 类_FBrowser_浏览器事件 :: 浏览器_拖拽区域改变
- 类_FBrowser_浏览器事件 :: 进程间消息_收到渲染进程消息
- 类_FBrowser_浏览器事件 :: 离屏渲染_获取根屏幕矩形
- 类_FBrowser_浏览器事件 :: 离屏渲染_获取视图矩形
- 类_FBrowser_浏览器事件 :: 离屏渲染_获取屏幕点
- 类_FBrowser_浏览器事件 :: 离屏渲染_获取窗口信息
- 类_FBrowser_浏览器事件 :: 离屏渲染_即将显示弹窗
- 类_FBrowser_浏览器事件 :: 离屏渲染_移动调整弹窗
- 类_FBrowser_浏览器事件 :: 离屏渲染_将被绘制
- 类_FBrowser_浏览器事件 :: 离屏渲染_将被加速绘制
- 类_FBrowser_浏览器事件 :: 离屏渲染_开始拖拽
- 类_FBrowser_浏览器事件 :: 离屏渲染_更新拖动光标
- 类_FBrowser_浏览器事件 :: 离屏渲染_滚动偏移量改变
- 类_FBrowser_浏览器事件 :: 离屏渲染_IME范围改变
- 类_FBrowser_浏览器事件 :: 离屏渲染_文本选择改变
- 类_FBrowser_浏览器事件 :: 离屏渲染_虚拟键盘请求
- 类_FBrowser_浏览器事件 :: 浏览器_即将创建主框架Document
- 类_FBrowser_浏览器事件 :: 浏览器_获取音频参数
- 类_FBrowser_浏览器事件 :: 浏览器_即将启动音频流
- 类_FBrowser_浏览器事件 :: 浏览器_收到音频流包
- 类_FBrowser_浏览器事件 :: 浏览器_即将结束音频流
- 类_FBrowser_浏览器事件 :: 浏览器_音频流出现错误
- 类_FBrowser_浏览器事件 :: 浏览器_即将执行Chrome命令
- 类_FBrowser_浏览器事件 :: 浏览器_即将创建框架
- 类_FBrowser_浏览器事件 :: 浏览器_即将连接框架
- 类_FBrowser_浏览器事件 :: 浏览器_即将拆离框架
- 类_FBrowser_浏览器事件 :: 浏览器_即将改变主框架
- 类_FBrowser_浏览器事件 :: 浏览器_即将请求媒体访问许可
- 类_FBrowser_浏览器事件 :: 浏览器_即将显示许可提示
- 类_FBrowser_浏览器事件 :: 浏览器_即将关闭许可提示
- 类_FBrowser_服务器事件 :: 服务器即将创建
- 类_FBrowser_服务器事件 :: 服务器即将销毁
- 类_FBrowser_开发者消息事件 :: 开发者消息_VIP_收到消息
- 类_FBrowser_开发者消息事件 :: 开发者消息_VIP_执行完成
- 类_FBrowser_开发者消息事件 :: 开发者消息_VIP_收到事件
- 类_FBrowser_开发者消息事件 :: 开发者消息_VIP_已附加
- 类_FBrowser_开发者消息事件 :: 开发者消息_VIP_已分离
- 类_FBrowser_URL请求事件 :: 下载进度
- 类_FBrowser_URL请求事件 :: 获得需授权证书
- 类_FBrowser_浏览器 :: 可否后退
- 类_FBrowser_浏览器 :: 关闭浏览器
- 类_FBrowser_浏览器 :: 下载图片
- 类_FBrowser_浏览器 :: 打印为PDF
- 类_FBrowser_浏览器 :: 停止查找
- 类_FBrowser_浏览器 :: 打开开发者工具
- 类_FBrowser_浏览器 :: 关闭开发者工具
- 类_FBrowser_浏览器 :: 进程间消息_发送数据_到全部渲染进程
- 类_FBrowser_浏览器 :: 进程间消息_发送数据_到指定渲染进程
- 类_FBrowser_浏览器 :: 进程间消息_取渲染进程数量
- 类_FBrowser_浏览器 :: 进程间消息_取渲染进程ID清单
- 类_FBrowser_浏览器 :: 进程间消息_发送数据_到主进程
- 类_FBrowser_浏览器 :: 离屏渲染_离屏渲染被禁用
- 类_FBrowser_浏览器 :: 离屏渲染_通知已被调整大小
- 类_FBrowser_浏览器 :: 离屏渲染_通知已被隐藏
- 类_FBrowser_浏览器 :: 离屏渲染_通知屏幕信息被改变
- 类_FBrowser_浏览器 :: 离屏渲染_使视图无效
- 类_FBrowser_浏览器 :: 离屏渲染_取帧率
- 类_FBrowser_浏览器 :: 离屏渲染_置帧率
- 类_FBrowser_浏览器 :: 离屏渲染_IME置组成
- 类_FBrowser_浏览器 :: 离屏渲染_IME置交互文本
- 类_FBrowser_浏览器 :: 离屏渲染_IME完成组合文本
- 类_FBrowser_浏览器 :: 离屏渲染_IME取消组合
- 类_FBrowser_浏览器 :: 离屏渲染_拖动进入
- 类_FBrowser_浏览器 :: 离屏渲染_拖动移动
- 类_FBrowser_浏览器 :: 离屏渲染_拖动离开
- 类_FBrowser_浏览器 :: 离屏渲染_拖动放下
- 类_FBrowser_浏览器 :: 离屏渲染_拖动结束位置
- 类_FBrowser_浏览器 :: 离屏渲染_拖动系统结束
- 类_FBrowser_基础框架 :: 执行JS代码
- 类_FBrowser_基础框架 :: 执行JS代码_带返回值
- 类_FBrowser_框架 :: 源码视图
- 类_FBrowser_命令行 :: VIP_高级_设置全局代理
- 类_FBrowser_请求环境 :: VIP_高级_载入插件路径
- 类_FBrowser_请求环境 :: VIP_高级_安装CRX插件包
- 类_FBrowser_请求环境 :: VIP_高级_卸载插件
- 类_FBrowser_请求环境 :: VIP_高级_取插件地址
- 类_FBrowser_请求环境 :: VIP_高级_取插件路径
- 类_FBrowser_请求环境 :: VIP_高级_取插件名
- 类_FBrowser_V8环境 :: 执行JS代码
- 类_FBrowser_读取流 :: 到指定偏移位置
- 类_FBrowser_填表框架 :: 点击元素
- 类_FBrowser_填表框架 :: 滚动到元素
- 类_FBrowser_填表框架 :: 元素是否存在
- 类_FBrowser_V8值 :: 指定环境执行函数
- FBrowserVIP注册 :: VIP注册_取机器码
- FBrowserVIP注册 :: VIP注册_取开始时间
- FBrowserVIP注册 :: VIP注册_取到期时间
- FBrowserVIP注册 :: VIP注册_取注册功能
- FBrowserVIP注册 :: VIP注册_取注册版本
- FBrowserVIP注册 :: VIP注册_取注册码类型
- FBrowserVIP注册 :: VIP注册_取目标系统平台
- FBrowserVIP注册 :: VIP注册_取错误信息
- FBrowserVIP注册 :: VIP注册_置授权码
- FBrowserVIP注册 :: VIP注册_生成本地授权文件
- 类_FBrowserVIP_控制器 :: WebSocket_启用拦截
- 类_FBrowserVIP_控制器 :: 开发者消息_发送消息
- 类_FBrowserVIP_控制器 :: 开发者消息_执行方法
- 类_FBrowserVIP_控制器 :: 开发者消息_启用监管者事件
- 类_FBrowserVIP_控制器 :: 开发者消息_关闭监管者事件
- 类_FBrowserVIP_控制器 :: 过滤器_修改内容
- 类_FBrowserVIP_控制器 :: 过滤器_取消修改内容
- 类_FBrowserVIP_控制器 :: 过滤器_取消全部修改内容
- 类_FBrowserVIP_控制器 :: 过滤器_替换资源_数据
- 类_FBrowserVIP_控制器 :: 过滤器_替换资源_文件
- 类_FBrowserVIP_控制器 :: 过滤器_取消替换资源
- 类_FBrowserVIP_控制器 :: 过滤器_取消全部替换资源