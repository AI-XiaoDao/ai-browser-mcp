# -*- coding: utf-8 -*-
r"""B2 — 中文成员名 -> 英文 PascalCase 合成器

策略: 贪婪最长匹配
  1) 先在 TERMS 里找最长可匹配的中文词 (2-8 字)
  2) 未命中则退回 CHARS 单字表
  3) ASCII 段原样保留并按 ACRONYMS 归一化大小写
  4) 连接为 PascalCase, 类内去重
输出未命中词素清单以便迭代补词典。
"""
import sys, os, re, json, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from vlib import *
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
import _console  # noqa: F401  控制台 UTF-8 兜底(见 _console.py)
OUT = os.path.dirname(os.path.abspath(__file__))

ACR = {"MCP", "URL", "V8", "JSON", "CDP", "IPC", "VIP", "TLS", "JS", "CSS", "HTML",
       "DOM", "XHR", "WS", "WSS", "HTTP", "HTTPS", "UA", "ID", "PDF", "CRX", "TCP",
       "SSL", "API", "RPC", "UI", "JSVMP", "XPATH", "MIME", "CRLF", "GBK", "UTF8",
       "SQL", "WAL", "TTL", "CPU", "GPU", "IP", "CORS", "HAR", "HMAC", "AES", "RSA",
       "MD5", "SHA", "BASE64", "UTF", "OK", "EOF", "NULL", "CRUD", "GA", "SDK"}

# ---- 术语词典(长词优先): 中文 -> 英文 token ----
TERMS = {
    # 动作动词
    "取": "Get", "置": "Set", "设": "Set", "加": "Add", "减": "Sub", "删除": "Delete",
    "移除": "Remove", "清空": "Clear", "清理": "Clean", "创建": "Create", "建立": "Create",
    "构建": "Build", "销毁": "Destroy", "关闭": "Close", "打开": "Open", "启动": "Start",
    "停止": "Stop", "暂停": "Pause", "恢复": "Resume", "继续": "Continue", "重启": "Restart",
    "注册": "Register", "注销": "Unregister", "挂载": "Attach", "卸载": "Detach",
    "发送": "Send", "接收": "Receive", "收到": "OnReceive", "提交": "Submit",
    "执行": "Execute", "运行": "Run", "调用": "Call", "分派": "Dispatch",
    "处理": "Handle", "解析": "Parse", "序列化": "Serialize", "反序列化": "Deserialize",
    "编码": "Encode", "解码": "Decode", "转义": "Escape", "反转义": "Unescape",
    "记录": "Record", "查询": "Query", "查找": "Find", "检索": "Search", "搜索": "Search",
    "存储": "Store", "保存": "Save", "读取": "Read", "写入": "Write", "载入": "Load",
    "加载": "Load", "下载": "Download", "上传": "Upload", "导入": "Import", "导出": "Export",
    "提取": "Extract", "设置": "Set", "获取": "Get", "获得": "Get", "得到": "Get",
    "检查": "Check", "验证": "Validate", "校验": "Verify", "确保": "Ensure", "确认": "Confirm",
    "判断": "Judge", "比较": "Compare", "匹配": "Match", "规范": "Normalize",
    "规范化": "Normalize", "转换": "Convert", "映射": "Map", "复制": "Copy", "移动": "Move",
    "更新": "Update", "刷新": "Refresh", "重置": "Reset", "应用": "Apply", "装配": "Apply",
    "启用": "Enable", "禁用": "Disable", "允许": "Allow", "拒绝": "Reject", "跳过": "Skip",
    "等待": "Wait", "延时": "Delay", "睡眠": "Sleep", "超时": "Timeout", "中断": "Interrupt",
    "退出": "Exit", "返回": "Return", "提交结果": "SubmitResult", "消费": "Consume",
    "修剪": "Trim", "裁剪": "Trim", "截断": "Truncate", "压缩": "Compress", "解压": "Decompress",
    "展开": "Expand", "折叠": "Collapse", "加入": "Add", "追加": "Append", "插入": "Insert",
    "打包": "Pack", "解包": "Unpack", "分配": "Allocate", "释放": "Release", "占用": "Acquire",
    "尝试": "Try", "确保可用": "EnsureAvailable", "自愈": "SelfHeal", "重试": "Retry",
    "注入": "Inject", "拦截": "Intercept", "篡改": "Tamper", "替换": "Replace",
    "过滤": "Filter", "收集": "Collect", "统计": "Count", "计算": "Compute",
    "排序": "Sort", "去重": "Dedup", "合并": "Merge", "拆分": "Split", "切分": "Split",
    "转": "To", "到": "To", "为": "To", "成": "To",
    # 名词 - 系统
    "浏览器": "Browser", "命令": "Command", "服务器": "Server", "客户端": "Client",
    "参数": "Param", "参数JSON": "ParamJson", "请求": "Request", "响应": "Response",
    "任务": "Task", "框架": "Frame", "文本": "Text", "标识": "Key", "消息": "Message",
    "方法名": "MethodName", "键名": "KeyName", "连接": "Connection", "回调": "Callback",
    "错误": "Error", "对象": "Object", "类型": "Type", "文件": "File", "路径": "Path",
    "文件路径": "FilePath", "数据": "Data", "数据指针": "DataPtr", "数据大小": "DataSize",
    "指针": "Ptr", "值": "Value", "结果": "Result", "结果指针": "ResultPtr",
    "结果大小": "ResultSize", "状态": "State", "状态码": "StatusCode", "代码": "Code",
    "事件": "Event", "事件名": "EventName", "事件类型": "EventType", "事件数据": "EventData",
    "数组": "Array", "列表": "List", "字典": "Dict", "表": "Table", "缓存": "Cache",
    "日志": "Log", "日志类型": "LogType", "地址": "Url", "链接": "Link", "主机": "Host",
    "端口": "Port", "域名": "Domain", "来源": "Source", "目标": "Target", "名称": "Name",
    "描述": "Description", "前缀": "Prefix", "后缀": "Suffix", "内容": "Content",
    "内容类型": "ContentType", "长度": "Length", "大小": "Size", "数量": "Count",
    "条数": "Count", "个数": "Count", "索引": "Index", "下标": "Index", "序号": "Seq",
    "毫秒": "Ms", "秒": "Sec", "分钟": "Minute", "时间": "Time", "时间戳": "Timestamp",
    "间隔": "Interval", "轮询": "Poll", "轮询间隔": "PollInterval", "上限": "Limit",
    "下限": "LowerBound", "最大值": "Max", "最小值": "Min", "最大": "Max", "最小": "Min",
    "最大毫秒": "MaxMs", "最大字符数": "MaxChars", "最大条数": "MaxCount",
    "最大等待": "MaxWait", "限制": "Limit", "限制条数": "LimitCount",
    # 名词 - 浏览器/CEF
    "页面": "Page", "标题": "Title", "窗口": "Window", "句柄": "Handle",
    "窗口句柄": "WindowHandle", "标签": "Tab", "地址栏": "UrlBar", "源码": "Source",
    "加载": "Load", "导航": "Navigate", "前进": "Forward", "后退": "Back",
    "刷新": "Reload", "渲染": "Render", "开发者": "DevTools", "开发者消息": "DevToolsMessage",
    "调试": "Debug", "调试器": "Debugger", "断点": "Breakpoint", "暂停": "Pause",
    "调用栈": "CallStack", "作用域": "Scope", "脚本": "Script", "脚本源码": "ScriptSource",
    "截图": "Screenshot", "打印": "Print", "下载": "Download", "触摸": "Touch",
    "鼠标": "Mouse", "键盘": "Keyboard", "按键": "Key", "点击": "Click", "滚动": "Scroll",
    "焦点": "Focus", "元素": "Element", "选择器": "Selector", "表单": "Form",
    "填表": "Form", "字段": "Field", "输入": "Input", "输出": "Output",
    "网络": "Network", "资源": "Resource", "请求头": "Header", "响应头": "ResponseHeader",
    "代理": "Proxy", "证书": "Certificate", "认证": "Auth", "凭据": "Credential",
    "下载接管": "DownloadHook", "方案": "Scheme", "菜单": "Menu", "快捷菜单": "ContextMenu",
    "弹窗": "Popup", "对话框": "Dialog", "全屏": "Fullscreen", "图标": "Favicon",
    "进度": "Progress", "音视频": "Media", "音频": "Audio", "视频": "Video", "声音": "Sound",
    "静音": "Mute", "音量": "Volume", "缩放": "Zoom", "分辨率": "Resolution",
    "指纹": "Fingerprint", "反检测": "AntiDetect", "持久反检测": "PersistentAntiDetect",
    "持久": "Persistent", "环境": "Environment", "配置": "Config", "选项": "Option",
    "属性": "Attribute", "风格": "Style", "样式": "Style", "窗口样式": "WindowStyle",
    "内核": "Kernel", "插件": "Extension", "扩展": "Extension",
    # 名词 - 本项目结构
    "分派": "Dispatch", "分类分派": "DispatchClass", "核心": "Core", "内核分派": "KernelDispatch",
    "系统": "System", "编排": "Workflow", "工作流": "Workflow", "逆向": "Reverse",
    "核心操作": "Core", "系统操作": "System", "运维": "Ops",
    "命令服务器": "CommandServer", "工具": "Tool", "工具名": "ToolName",
    "同步等待": "SyncWait", "异步": "Async", "异步结果": "AsyncResult",
    "等待任务": "WaitTask", "线程": "Thread", "锁": "Lock", "互斥": "Mutex",
    "原子": "Atomic", "队列": "Queue", "槽": "Slot", "请求槽": "RequestSlot",
    "监控": "Monitor", "观察者": "Observer", "反应器": "Reactor", "探针": "Probe",
    "监视": "Watch", "定时": "Timer", "定时监视": "TimerWatch", "追踪": "Trace",
    "插桩": "Instrument", "钩子": "Hook", "钩": "Hook", "算法": "Algorithm",
    "函数": "Function", "变量": "Variable", "全局": "Global", "局部": "Local",
    "内部": "Internal", "外部": "External", "安全": "Safe", "危险": "Dangerous",
    "默认": "Default", "当前": "Current", "上次": "Last", "本次": "This", "下一个": "Next",
    "上一个": "Prev", "首个": "First", "最后": "Last", "全部": "All", "所有": "All",
    "空": "Empty", "非空": "NonEmpty", "有效": "Valid", "无效": "Invalid",
    "可用": "Available", "已注册": "Registered", "已持锁": "LockHeld", "已打开": "Opened",
    "已关闭": "Closed", "已释放": "Released", "已成功": "Succeeded", "已完成": "Done",
    "是否": "Is", "能否": "Can", "可否": "Can", "需要": "Need", "应": "Should",
    "成功": "Success", "失败": "Failure", "是否成功": "IsSuccess", "错误消息": "ErrorMessage",
    "错误代码": "ErrorCode", "错误文本": "ErrorText", "错误码": "ErrorCode",
    "提示": "Hint", "帮助": "Help", "说明": "Description", "注释": "Comment",
    "文档": "Doc", "根目录": "RootDir", "目录": "Dir", "运行目录": "RunDir",
    "服务器实例": "ServerInstance", "连接ID": "ConnectionId", "客户端地址": "ClientAddr",
    "地址指向": "Address", "指向": "Ptr",
    "密钥": "Key", "授权码": "LicenseCode", "版本": "Version", "协议": "Protocol",
    "速率": "Rate", "速率限制": "RateLimit", "限流": "RateLimit",
    "维护": "Maintain", "定期维护": "PeriodicMaintain", "节拍": "Tick", "主循环": "MainLoop",
    "循环": "Loop", "消息泵": "MessagePump", "关闭序列": "ShutdownSequence",
    "退出": "Exit", "应退出": "ShouldExit", "正在退出": "IsExiting",
    "崩溃": "Crash", "恢复": "Recovery", "重建": "Rebuild", "欢迎页": "WelcomePage",
    "扩展名": "Extension", "MIME类型": "MimeType", "静态": "Static", "动态": "Dynamic",
    # ---- 第二批补充 (依据未命中统计) ----
    "容器": "Container", "常量": "Const", "标记": "Mark", "最新": "Latest",
    "完成": "Done", "载入结束": "LoadEnd", "载入开始": "LoadStart", "加载中": "Loading",
    "发起": "Start", "已发起": "Started", "布局": "Layout", "变体": "Variant",
    "双变体": "DualVariant", "批量": "Batch", "操作": "Op", "本机": "Local",
    "自托管": "SelfHosted", "带参数": "WithParams", "网页": "Web", "就绪": "Ready",
    "截至": "Until", "结束": "End", "开始": "Start", "中": "", "批量": "Batch",
    "单实例": "SingleInstance", "互斥体": "Mutex", "互斥锁": "Mutex", "自动恢复": "AutoResume",
    "恢复": "Restore", "崩溃恢复": "CrashRestore", "已恢复": "Restored",
    "处理器": "Handler", "过滤器": "Filter", "观察者": "Observer", "管理器": "Manager",
    "控制器": "Controller", "构建器": "Builder", "解析器": "Parser", "分发器": "Dispatcher",
    "调度器": "Scheduler", "桥": "Bridge", "桥接": "Bridge", "包装": "Wrapper",
    "序列": "Sequence", "阶段": "Phase", "步骤": "Step", "环节": "Stage",
    "条件": "Condition", "规则": "Rule", "策略": "Policy", "模式": "Mode",
    "开关": "Switch", "标志": "Flag", "标记位": "Flag", "位标": "Flag",
    "初始": "Init", "初始化": "Initialize", "完成度": "Progress",
    "反序列": "Deserialize", "序列化": "Serialize", "编码器": "Encoder",
    "阈值": "Threshold", "容量": "Capacity", "配额": "Quota", "预算": "Budget",
    "计数": "Count", "计数器": "Counter", "累加": "Accumulate", "递减": "Decrement",
    "递增": "Increment", "自增": "Increment", "自减": "Decrement",
    "递归": "Recursive", "迭代": "Iterate", "遍历": "Traverse", "枚举": "Enumerate",
    "包含": "Contains", "排除": "Exclude", "存在": "Exists", "不存在": "NotExists",
    "后": "After", "前": "Before", "存在后": "AfterExists", "即将": "Will",
    "通用": "Generic", "专用": "Dedicated", "特定": "Specific", "指定": "Specified",
    "图片": "Image", "图像": "Image", "服务": "Service", "服务器": "Server",
    "线程池": "ThreadPool", "线程": "Thread", "进程": "Process", "子进程": "ChildProcess",
    "父进程": "ParentProcess", "渲染进程": "Renderer", "主进程": "MainProcess",
    "渲染": "Render", "宿主": "Host", "客户端": "Client", "服务端": "Server",
    "机器码": "MachineCode", "授权": "License", "注册码": "RegCode", "功能": "Feature",
    "起始": "Start", "终止": "Stop", "截止": "Deadline", "持续": "Duration",
    "时长": "Duration", "时长毫秒": "DurationMs", "剩余": "Remaining", "已用": "Elapsed",
    "已耗": "Elapsed", "预算毫秒": "BudgetMs",
    "行文本": "LineText", "多行": "MultiLine", "单行": "SingleLine", "空行": "BlankLine",
    "字符": "Char", "字符集": "Charset", "字符串": "String", "字节": "Byte",
    "字节集": "Bytes", "字节数": "ByteCount", "位": "Bit", "字节大小": "ByteSize",
    "合法": "Legal", "非法": "Illegal", "严格": "Strict", "宽松": "Loose",
    "统一": "Unified", "单独": "Separate", "独立": "Independent", "共享": "Shared",
    "只读": "ReadOnly", "可写": "Writable", "可变": "Mutable", "不可变": "Immutable",
    "首选": "Preferred", "备选": "Backup", "回退": "Fallback", "降级": "Degrade",
    "兜底": "Fallback", "快照": "Snapshot", "副本": "Copy", "镜像": "Mirror",
    "来源地址": "SourceUrl", "目标地址": "TargetUrl", "回环": "Loopback",
    "本机地址": "LocalAddress", "绑定地址": "BindAddress", "绑定": "Bind",
    "端口号": "Port", "主机名": "HostName", "子域": "SubDomain",
    "大小写": "Case", "小写": "LowerCase", "大写": "UpperCase", "敏感": "Sensitive",
    "忽略": "Ignore", "强制": "Force", "可选": "Optional", "必须": "Required",
    "必填": "Required", "默认值": "Default", "默认": "Default",
    "首次": "First", "末次": "Last", "本次": "Current", "上次": "Last",
    "下次": "Next", "曾经": "Ever", "从未": "Never", "始终": "Always",
    "偶尔": "Occasionally", "经常": "Often", "频繁": "Frequent",
    # ---- 第三批: 修复"被逐字拆译"的词组 (依据 b5 缺口清单) ----
    "方法": "Method", "控制台": "Console", "流程": "Workflow", "上下文": "Context",
    "表达式": "Expression", "求值": "Evaluate", "用户": "User", "动作": "Action",
    "手势": "Gesture", "成员": "Member", "次数": "Count", "一次": "Once",
    "添加": "Add", "填充": "Fill", "基础": "Base", "定义": "Definition",
    "整数": "Int", "原始": "Raw", "需要": "Need", "禁用": "Disable",
    "自动化": "Automation", "检测": "Detect", "伪装": "Spoof", "安装": "Install",
    "代理": "Proxy", "累积": "Accumulate", "关键词": "Keyword", "正整数": "PositiveInt",
    "摘要": "Summary", "片段": "Fragment", "管理": "Manage", "完毕": "Done",
    "同步": "Sync", "条目": "Entry", "过期": "Expired", "逻辑": "Logic",
    "简单": "Simple", "行数": "LineCount", "详细": "Detailed", "短名": "ShortName",
    "正在": "Is", "嵌套": "Nested", "总数": "Total", "级别": "Level",
    "项数": "ItemCount", "滞留": "Stalled", "结构": "Structure", "相对": "Relative",
    "断开": "Disconnect", "读入": "ReadIn", "单步": "Step", "一行": "OneLine",
    "平行": "Parallel", "访问": "Access", "修改": "Modify", "标准": "Standard",
    "密码": "Password", "禁止": "Forbid", "自动": "Auto", "节流": "Throttle",
    "实例": "Instance", "尾部": "Tail", "行号": "LineNo", "模板": "Template",
    "信息": "Info", "头部": "Head", "帧内": "InFrame", "小数": "Float",
    "清零": "Zero", "并行": "Concurrent", "意外": "Unexpected", "离开": "Leave",
    "返馈": "Feedback", "拆离": "Detach", "失去": "Lose", "紧凑": "Compact",
    "宽度": "Width", "高度": "Height", "墙钟": "WallClock", "活动": "Active",
    "账号": "Account", "近期": "Recent", "改变": "Change", "附着": "Attach",
    "屏蔽": "Block", "冷却": "Cooldown", "格式": "Format", "首项": "FirstItem",
    "即时": "Immediate", "快读": "FastRead", "绝对": "Absolute", "每天": "PerDay",
    "因子": "Factor", "单条": "SingleItem", "并发": "Concurrency", "保留": "Retain",
    "缺少": "Missing", "程序": "Program", "异常": "Exception", "节点": "Node",
    "名基": "NameBase", "分片": "Shard", "需放": "NeedRelease", "新行": "NewLine",
    "原文": "RawText", "必需": "Required", "弹出": "Popup", "过渡": "Transition",
    "重载": "Reload", "接受": "Accept", "选择": "Select", "顺序": "Order",
    "尺寸": "Size", "编辑": "Edit", "透传": "Passthrough", "重定向": "Redirect",
    "自定义": "Custom", "长整数": "Int64", "里程碑": "Milestone", "元信息": "Meta",
    "缓冲区": "Buffer", "保留天数": "RetentionDays", "额外信息": "ExtraInfo",
    "捕获异常": "CatchException", "生命周期": "Lifecycle", "堆栈踪迹": "StackTrace",
    "自动安装": "AutoInstall", "重定向链": "RedirectChain", "保留缓冲": "RetentionBuffer",
    "不支持的": "Unsupported", "预估耗时": "EstimatedElapsed", "放弃原因": "AbandonReason",
    "被改变": "Changed",
    # ---- 第四批: 长名与残留别扭点 ----
    "转为": "To", "转成": "To", "转换为": "To", "取走": "Consume",
    "被忽略": "Ignored", "忽略": "Ignore", "走后": "After",
    "响应构建": "ResponseBuilder", "启动方法": "StartMethod", "入口方法": "EntryMethod",
    "将": "Convert", "必须为": "MustBe", "脚本行": "ScriptLine", "必须": "Must",
}

# ---- 单字兜底表 ----
CHARS = {
    "取": "Get", "置": "Set", "加": "Add", "删": "Del", "查": "Query", "写": "Write",
    "读": "Read", "发": "Send", "收": "Recv", "开": "Open", "关": "Close", "停": "Stop",
    "启": "Start", "转": "To", "到": "To", "为": "To", "的": "", "地": "",
    "是": "Is", "否": "Not", "能": "Can", "要": "Need", "应": "Should", "须": "Must",
    "大": "Big", "小": "Small", "长": "Long", "短": "Short", "新": "New", "旧": "Old",
    "高": "High", "低": "Low", "快": "Fast", "慢": "Slow", "多": "Multi", "少": "Few",
    "前": "Prev", "后": "Next", "头": "Head", "尾": "Tail", "内": "Inner", "外": "Outer",
    "上": "Upper", "下": "Lower", "左": "Left", "右": "Right", "中": "Mid",
    "主": "Main", "子": "Sub", "总": "Total", "全": "All", "空": "Empty", "满": "Full",
    "名": "Name", "值": "Value", "数": "Num", "量": "Amount", "率": "Rate",
    "表": "Table", "项": "Item", "位": "Bit", "层": "Layer", "级": "Level",
    "行": "Row", "列": "Col", "页": "Page", "段": "Seg", "块": "Block", "组": "Group",
    "类": "Class", "型": "Type", "式": "Mode", "法": "Method", "器": "Device",
    "池": "Pool", "栈": "Stack", "队": "Queue", "树": "Tree", "图": "Graph",
    "锁": "Lock", "键": "Key", "码": "Code", "位号": "Id", "号": "No", "序": "Seq",
    "错": "Err", "误": "Err", "常": "Normal", "异": "Abnormal",
    "真": "True", "假": "False", "零": "Zero", "一": "One", "二": "Two", "三": "Three",
    "已": "Has", "未": "Not", "正": "Is", "待": "Pending", "将": "Will",
    "得": "Got", "给": "Give", "让": "Let", "被": "Be", "把": "Take",
    "个": "", "些": "", "之": "", "与": "And", "和": "And", "或": "Or", "非": "Not",
    "每": "Per", "各": "Each", "某": "Some", "此": "This", "该": "The",
    # ---- 单字兜底第二批 (依据未命中统计补齐, 共 193 字) ----
    "改": "Modify", "变": "Change", "源": "Source", "定": "Fixed", "原": "Original",
    "步": "Step", "动": "Dynamic", "整": "Whole", "自": "Auto", "库": "Lib",
    "始": "Start", "单": "Single", "片": "Slice", "帧": "Frame", "并": "And",
    "留": "Keep", "重": "Re", "节": "Section", "信": "Msg", "息": "Info",
    "期": "Period", "摘": "Summary", "求": "Request", "同": "Same", "控": "Control",
    "制": "Control", "台": "Station", "装": "Install", "管": "Manage", "理": "Manage",
    "向": "To", "条": "Item", "方": "Way", "完": "Done", "毕": "Done",
    "程": "Process", "义": "Meaning", "部": "Part", "过": "Past", "清": "Clear",
    "可": "Can", "流": "Stream", "体": "Body", "文": "Text", "带": "With",
    "辑": "Logic", "安": "Safe", "用": "Use", "户": "User", "目": "Target",
    "保": "Keep", "点": "Point", "额": "Amount", "从": "From", "化": "Convert",
    "需": "Need", "放": "Release", "逻": "Logic", "员": "Member", "简": "Simple",
    "作": "Do", "详": "Detail", "细": "Fine", "别": "Other", "对": "To",
    "入": "In", "在": "At", "修": "Fix", "嵌": "Embed", "套": "Set",
    "天": "Day", "不": "Not", "堆": "Heap", "踪": "Trace", "迹": "Trace",
    "基": "Base", "除": "Del", "持": "Hold", "生": "Gen", "模": "Mode",
    "板": "Board", "词": "Word", "滞": "Stall", "结": "End", "构": "Struct",
    "时": "Time", "添": "Add", "附": "Attach", "相": "Phase", "断": "Break",
    "平": "Flat", "无": "No", "访": "Visit", "问": "Ask", "禁": "Forbid",
    "止": "Stop", "离": "Leave", "次": "Times", "透": "Transparent", "传": "Pass",
    "弃": "Abandon", "因": "Cause", "标": "Mark", "准": "Standard", "链": "Chain",
    "度": "Degree", "密": "Dense", "首": "First", "缓": "Cache", "冲": "Flush",
    "实": "Real", "例": "Instance", "捕": "Catch", "获": "Get", "间": "Interval",
    "排": "Arrange", "分": "Divide", "达": "Reach", "现": "Current", "走": "Walk",
    "示": "Show", "跟": "Follow", "随": "Along", "预": "Pre", "估": "Estimate",
    "耗": "Elapsed", "础": "Base", "以": "By", "仅": "Only", "填": "Fill",
    "充": "Fill", "双": "Dual", "必": "Must", "含": "Contain", "里": "Inside",
    "碑": "Stone", "推": "Push", "荐": "Recommend", "意": "Intent", "手": "Hand",
    "势": "Gesture", "弹": "Popup", "出": "Out", "栏": "Bar", "渡": "Transition",
    "载": "Load", "接": "Connect", "受": "Receive", "返": "Return", "馈": "Feedback",
    "选": "Select", "择": "Select", "顺": "Sequential", "拆": "Detach", "按": "Press",
    "捷": "Shortcut", "失": "Lose", "去": "Remove", "尺": "Ruler", "寸": "Size",
    "编": "Edit", "元": "Element", "据": "Data", "紧": "Tight", "凑": "Compact",
    "顶": "Top", "宽": "Width", "墙": "Wall", "钟": "Clock", "活": "Active",
    "账": "Account", "检": "Check", "测": "Measure", "伪": "Fake", "近": "Near",
    "命": "Command", "周": "Cycle", "桶": "Bucket", "着": "On", "区": "Zone",
    "屏": "Screen", "蔽": "Block", "冷": "Cold", "却": "Cool", "态": "State",
    "格": "Format", "即": "Immediate", "累": "Accumulate", "积": "Accumulate",
    "绝": "Absolute", "衰": "Decay", "缺": "Missing", "支": "Support",
}


def norm_ascii(tok):
    u = tok.upper()
    if u in ACR:
        return u
    return tok[:1].upper() + tok[1:].lower() if tok.isalpha() else tok


ASCII_SPLIT = re.compile(r"[A-Z]+(?![a-z])|[A-Z][a-z]+|[a-z]+|[0-9]+")


def split_ascii(txt):
    """把 ASCII 段按 下划线 / 驼峰 / 字母数字边界 切开, 再按缩写表归一"""
    out = []
    for seg in re.split(r"_+", txt):
        if not seg:
            continue
        if seg.upper() in ACR:
            out.append(seg.upper()); continue
        for part in ASCII_SPLIT.findall(seg):
            if not part:
                continue
            if part.isupper() and len(part) >= 2:
                out.append(part)          # 已是缩写, 原样保留 (JSONRPC/CDP/WS...)
            elif part.upper() in ACR:
                out.append(part.upper())
            elif part.isdigit():
                out.append(part)
            else:
                out.append(part[:1].upper() + part[1:].lower())
    return out


def has_cn(s):
    return re.search(r"[\u4e00-\u9fff]", s) is not None


def split_tokens(name):
    """把成员名切成 [('cn'|'ascii', 文本)]"""
    out, i, n = [], 0, len(name)
    while i < n:
        c = name[i]
        if re.match(r"[\u4e00-\u9fff]", c):
            j = i
            while j < n and re.match(r"[\u4e00-\u9fff]", name[j]):
                j += 1
            out.append(("cn", name[i:j])); i = j
        else:
            j = i
            while j < n and not re.match(r"[\u4e00-\u9fff]", name[j]):
                j += 1
            out.append(("ascii", name[i:j])); i = j
    return out


unmapped = collections.Counter()

def cn_to_tokens(run):
    """贪婪最长匹配"""
    res, i, n = [], 0, len(run)
    while i < n:
        hit = None
        for L in range(min(8, n - i), 0, -1):
            seg = run[i:i + L]
            if seg in TERMS:
                hit = (L, TERMS[seg]); break
            if L == 1 and seg in CHARS:
                hit = (1, CHARS[seg]); break
        if hit is None:
            unmapped[run[i]] += 1
            res.append("X" + run[i]); i += 1
        else:
            L, en = hit
            if en:
                res.append(en)
            i += L
    return res


def compose(name):
    toks = []
    for kind, txt in split_tokens(name):
        if kind == "cn":
            toks.extend(cn_to_tokens(txt))
        else:
            toks.extend(split_ascii(txt))
    s = "".join(toks)
    s = re.sub(r"[^0-9A-Za-z]", "", s)
    if not s:
        s = "Member"
    if s[0].isdigit():
        s = "N" + s
    return s


def compose_class(name):
    """类名: 去掉 类_ 前缀后合成"""
    n = name[2:] if name.startswith("类_") else name
    return compose(n)


if __name__ == "__main__":
    inv = json.load(open(os.path.join(OUT, "inventory.json"), encoding="utf-8"))
    # 先全量跑一遍收集未命中词素
    for c in inv["classes"]:
        compose_class(c["name"])
    for m in inv["methods"]:
        compose(m["name"])
        for p in [x for x in inv["params"] if x["cls"] == m["cls"] and x["method"] == m["name"]]:
            compose(p["name"])
    for v in inv["vars"]:
        compose(v["name"])

    print("=" * 96)
    print("B2 英文名合成 — 抽样 (修订版)")
    print("=" * 96)
    print()
    print("--- 类名 ---")
    for c in inv["classes"]:
        print("  %-30s -> %-40s %s" % (c["name"], compose_class(c["name"]),
                                       "【保留】" + c["keep_reason"] if c["keep"] else ""))
    print()
    print("--- 方法抽样 (40) ---")
    shown = 0
    for m in inv["methods"]:
        if m["keep"]:
            continue
        print("  %-28s %-32s -> %s" % (m["cls"][:28], m["name"], compose(m["name"])))
        shown += 1
        if shown >= 40:
            break
    print()
    print("--- 变量抽样 (20) ---")
    for v in inv["vars"][:20]:
        print("  %-28s %-30s -> %s" % (v["cls"][:28], v["name"], compose(v["name"])))
    print()
    print("--- 参数抽样 (20) ---")
    for p in inv["params"][:20]:
        print("  %-28s %-30s -> %s" % (p["method"][:28], p["name"], compose(p["name"])))
    print()
    print("=" * 96)
    print("未命中词素 全量 (%d 个, 按频次降序):" % len(unmapped))
    print("=" * 96)
    for k, v in unmapped.most_common():
        print("   %s x%d" % (k, v), end="")
    print()
