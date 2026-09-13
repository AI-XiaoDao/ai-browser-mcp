#pragma once
#ifndef ELIBTYPES_H_
#define ELIBTYPES_H_

#include <windows.h>
#include <list>
#include "include/wrapper/cef_message_router.h"
#include "FBroBaseType.h"

#ifdef _FBROELIB
// 易类枚举
typedef enum
{
	EClassMinValue = 10001,

	ECommandLine = EClassMinValue,
	EBrowser,
	EFrame,
	EImage,
	ERequest,
	EPostData,
	EPostDataElement,
	EResponse,
	ERequestContext,
	ECookieManager,
	EDragData,
	EX509CertPrincipal,
	EX509Certificate,
	ESSLInfo,
	EProcessMessage,
	EListValue,
	EMenuModel,
	EContextMenuParams,
	EDownloadItem,
	EBeforeDownloadCallback,
	EDownloadItemCallback,
	EFileDialogCallback,
	EJSDialogCallback,
	EAuthCallback,
	EDictionaryValue,
	EValue,

	EV8Context,
	EV8Exception,
	EV8StackTrace,
	EDOMNode,
	EV8Value,
	ETaskRunner,
	EV8StackFrame,
	EDOMDocument,
	EExtension,

	EServer,
	EFBroWebsocket,
	EBinaryValue,

	ERunQuickMenuCallback,
	EMediaAccessCallback,
	EPermissionPromptCallback,
	EPrintSettings,
	EPrintDialogCallback,
	EPrintJobCallback,
	ESharedMemoryRegion,

	EFBroDOMWssClient,

	EFBroVIPControl,

	EFBroUseExtraData,

	EURLRequest,

	EFBroVIPVIPUserAgentData,

	EClassMaxValue = EFBroVIPVIPUserAgentData

} EClassName;

typedef enum
{
	FinishShutdown = 19999,//框架关闭结束事件
	OnClearData = 20000, // 清理数据标识，易专用
	OnContextInitialized = 20001,
	OnBeforeCommandLineProcessing,
	OnAfterCreated,
	OnBeforeBrowse,
	OnBeforeClose,
	OnAddressChange,
	OnTitleChange,
	OnTooltip,
	OnStatusMessage,
	OnFaviconURLChange,
	OnFullscreenModeChange,
	OnBeforePopup,
	DoClose,
	OnConsoleMessage,
	OnAutoResize,
	OnLoadingProgressChange,
	OnBeforeResourceLoad,
	OnResourceRedirect,
	OnResourceResponse,
	OnResourceLoadComplete,
	OnProtocolExecution,
	OnOpenURLFromTab, // 从标签打开URL
	OnQuotaRequest,	  // JS请求存储配额
	OnCertificateError,
	OnPluginCrashed,   // 插件意外崩溃
	OnRenderViewReady, // 渲染视图
	OnRenderProcessTerminated,
	OnLoadingStateChange, // 读取状态改变
	OnLoadStart,		  // 开始读取
	OnLoadEnd,			  // 读取完毕
	OnLoadError,		  // 读取错误
	OnProcessMessageReceived,
	OnBeforeContextMenu,
	RunContextMenu,
	OnContextMenuCommand,
	OnContextMenuDismissed,
	OnBeforeDownload,
	OnDownloadUpdated,
	OnPreKeyEvent,
	OnKeyEvent,
	OnFileDialog,
	OnJSDialog,
	OnBeforeUnloadDialog,
	OnResetDialogState,
	OnDialogClosed,
	OnTakeFocus,
	OnSetFocus,
	OnGotFocus,
	OnFindResult,
	GetAuthCredentials,
	OnDragEnter,
	OnDraggableRegionsChanged,
	GetResourceResponseFilter,
	OnBrowserCreated,
	FBroApp_OnProcessMessageReceived,
	GetRootScreenRect,
	GetViewRect,
	GetScreenPoint,
	GetScreenInfo,
	OnPopupShow,
	OnPopupSize,
	OnPaint,
	OnAcceleratedPaint,
	OnCursorChange,
	StartDragging,
	UpdateDragCursor,
	OnScrollOffsetChanged,
	OnImeCompositionRangeChanged,
	OnTextSelectionChanged,
	OnVirtualKeyboardRequested,

	GetResourceHandler,
	ResourceHandler_Open,
	ResourceHandler_ProcessRequest,
	ResourceHandler_GetResponseHeaders,
	ResourceHandler_Skip,
	ResourceHandler_Read,
	ResourceHandler_Cancel,

	OnRegisterCustomSchemes,
	OnBeforeChildProcessLaunch,
	OnRenderProcessThreadCreated,
	OnScheduleMessagePumpWork,
	OnRenderThreadCreated,
	OnWebKitInitialized,
	OnBrowserDestroyed,
	OnContextCreated,
	OnContextReleased,
	OnUncaughtException,
	OnFocusedNodeChanged,

	Render_OnLoadingStateChange,
	Render_OnLoadStart,
	Render_OnLoadEnd,
	Render_OnLoadError

	,
	Extension_OnExtensionLoadFailed,
	Extension_OnExtensionLoaded,
	Extension_OnExtensionUnloaded,
	Extension_OnBeforeBackgroundBrowser,
	Extension_OnBeforeBrowser,
	Extension_GetActiveBrowser,
	Extension_CanAccessBrowser,
	Extension_GetExtensionResource

	,
	Render_OnWebSocketCreate,
	Render_OnWebSocketClose,
	Render_OnWebSocketConnect,
	Render_OnWebSocketSendText,
	Render_OnWebSocketSendData,
	Render_OnWebSocketMessage

	,
	Message_OnReceiveRenderProcessMessage,
	Message_OnReceiveMainProcessMessage

	// 新内核增加
	,
	OnDocumentAvailableInMainFrame,
	OnMediaAccessChange,
	RunQuickMenu,
	OnQuickMenuCommand,
	OnQuickMenuDismissed,
	CanDownload,
	GetAudioParameters,
	OnAudioStreamStarted,
	OnAudioStreamPacket,
	OnAudioStreamStopped,
	OnAudioStreamError,
	OnChromeCommand,
	OnFrameCreated,
	OnFrameAttached,
	OnFrameDetached,
	OnMainFrameChanged,
	OnRequestMediaAccessPermission,
	OnShowPermissionPrompt,
	OnDismissPermissionPrompt

	// 自行添加事件
	,
	Extension_OnExtensionLoadFailedMessage
	// 插件获取tab默认浏览器事件
	,
	Extension_GetDefaultTabBrowser
	// 插件client事件
	,
	ExtensionClient_OnConsoleMessage,
	ExtensionClient_OnAfterCreated,
	ExtensionClient_OnBeforePopup,
	ExtensionClient_DoClose,
	ExtensionClient_OnBeforeClose

	,
	URLRequest_Start,
	URLRequest_End,
	URLRequest_OnRequestComplete,
	URLRequest_OnUploadProgress,
	URLRequest_OnDownloadProgress,
	URLRequest_OnDownloadData,
	URLRequest_GetAuthCredentials,

	//135内核后新加APP的事件
	OnGetDefaultClient,

	//135内核后新加client的事件
	OnBeforePopupAborted,
	OnBeforeDevToolsPopup,

	// my add 20260509 插件创建成功的事件
	OnCreateExtension,

	// my add 20260509 插件创建失败的事件
	OnCreateExtensionError,

	// my add 20260512 添加插件
	OnAddExtension,

	// my add 20260512 移除插件
	OnRemoveExtension,

	OnRequestContextInitialized

} EBroEvent;


// 类回调函数结构定义
typedef void(CALLBACK* OnPdfPrintFinished_callback)(int, const char*, BOOL);
typedef void(CALLBACK* OnDownloadImageFinished_callback)(int, const char*, int, HANDLE);
typedef void(CALLBACK* OnFileDialogDismissed_callback)(int, const char*);

typedef void(CALLBACK* StringVisitor_callback)(int, int, const char*); // 异步数据获取回调

// 执行JS取返回值回调
typedef void(CALLBACK* ExecuteJavaScript_callback)(int, int, int, const char*, BOOL, double, const char*);

// 事件回调函数结构定义
// 浏览器进程中执行,有的渲染进程中也会执行,待验证
typedef void(CALLBACK* FinishShutdown_Callback)(BOOL&);
typedef void(CALLBACK* OnClearData_callback)(HANDLE);
typedef void(CALLBACK* OnContextInitialized_callback)();
typedef void(CALLBACK* OnBeforeCommandLineProcessing_callback)(const char*, HANDLE);
typedef void(CALLBACK* OnAfterCreated_callback)(HANDLE, HANDLE);
typedef bool(CALLBACK* OnBeforeBrowse_callback)(HANDLE, HANDLE, HANDLE, BOOL, BOOL);
typedef void(CALLBACK* OnBeforeClose_callback)(HANDLE);
typedef void(CALLBACK* OnAddressChange_callback)(HANDLE, HANDLE, const char*);
typedef void(CALLBACK* OnTitleChange_callback)(HANDLE, const char*);
typedef bool(CALLBACK* OnTooltip_callback)(HANDLE, HANDLE);
typedef void(CALLBACK* OnStatusMessage_callback)(HANDLE, const char*);
typedef void(CALLBACK* OnFaviconURLChange_callback)(HANDLE, HANDLE);
typedef void(CALLBACK* OnFullscreenModeChange_callback)(HANDLE, bool);
typedef BOOL(CALLBACK* OnBeforePopup_callback)(HANDLE, HANDLE, int, const char*, const char*, int, BOOL, HANDLE, HANDLE, HANDLE, BOOL&, HANDLE); // 即将跳转新窗口

typedef void(CALLBACK* OnBeforePopupAborted_callback)(HANDLE, int);
typedef void(CALLBACK* OnBeforeDevToolsPopup_callback)(HANDLE, HANDLE, HANDLE, BOOL&, BOOL&, HANDLE);

typedef BOOL(CALLBACK* DoClose_callback)(HANDLE);																						// 执行关闭
typedef BOOL(CALLBACK* OnConsoleMessage_callback)(HANDLE, int, const char*, const char*, int);													// 控制台消息
typedef BOOL(CALLBACK* OnAutoResize_callback)(HANDLE, int, int);																		// 自动调整
typedef void(CALLBACK* OnLoadingProgressChange_callback)(HANDLE, int);																	// 读取进度变更
typedef BOOL(CALLBACK* OnBeforeResourceLoad_callback)(HANDLE, HANDLE, HANDLE);															// 即将加载资源
typedef void(CALLBACK* OnResourceRedirect_callback)(HANDLE, HANDLE, HANDLE, HANDLE, HANDLE);
typedef BOOL(CALLBACK* OnResourceResponse_callback)(HANDLE, HANDLE, HANDLE, HANDLE);
typedef void(CALLBACK* OnResourceLoadComplete_callback)(HANDLE, HANDLE, HANDLE, HANDLE, int, int); // 资源加载完毕
typedef void(CALLBACK* OnProtocolExecution_callback)(HANDLE, HANDLE, HANDLE, BOOL&);
typedef BOOL(CALLBACK* OnOpenURLFromTab_callback)(HANDLE, HANDLE, const char*, int, BOOL);	// 从标签打开URL
typedef BOOL(CALLBACK* OnQuotaRequest_callback)(HANDLE, const char*, int64_t);					// JS请求存储配额
typedef BOOL(CALLBACK* OnCertificateError_callback)(HANDLE, int, const char*, HANDLE);		// 请求证书错误
typedef void(CALLBACK* OnPluginCrashed_callback)(HANDLE, const char*);						// 插件意外崩溃
typedef void(CALLBACK* OnRenderViewReady_callback)(HANDLE);								// 渲染视图
typedef void(CALLBACK* OnRenderProcessTerminated_callback)(HANDLE, int, int, const char*);				// 渲染意外终止
typedef void(CALLBACK* OnLoadingStateChange_callback)(HANDLE, BOOL, BOOL, BOOL);		// 读取状态改变
typedef void(CALLBACK* OnLoadStart_callback)(HANDLE, HANDLE, int);					// 开始读取
typedef void(CALLBACK* OnLoadEnd_callback)(HANDLE, HANDLE, int);						// 读取完毕
typedef void(CALLBACK* OnLoadError_callback)(HANDLE, HANDLE, int, const char*, const char*);		// 读取错误
typedef BOOL(CALLBACK* OnProcessMessageReceived_callback)(HANDLE, HANDLE, int, HANDLE); // 浏览器进程收到消息
typedef void(CALLBACK* OnBeforeContextMenu_callback)(HANDLE, HANDLE, HANDLE, HANDLE);
typedef BOOL(CALLBACK* RunContextMenu_callback)(HANDLE, HANDLE, HANDLE, HANDLE);
typedef BOOL(CALLBACK* OnContextMenuCommand_callback)(HANDLE, HANDLE, HANDLE, int, int);
typedef void(CALLBACK* OnContextMenuDismissed_callback)(HANDLE, HANDLE);
typedef BOOL(CALLBACK* OnBeforeDownload_callback)(HANDLE, HANDLE, const char*, HANDLE);
typedef void(CALLBACK* OnDownloadUpdated_callback)(HANDLE, HANDLE, HANDLE);
typedef BOOL(CALLBACK* OnPreKeyEvent_callback)(HANDLE, HANDLE, HANDLE, BOOL);
typedef BOOL(CALLBACK* OnKeyEvent_callback)(HANDLE, HANDLE, HANDLE);
typedef BOOL(CALLBACK* OnFileDialog_callback)(HANDLE, int, const char*, const char*, HANDLE, HANDLE, HANDLE, HANDLE);
typedef BOOL(CALLBACK* OnJSDialog_callback)(HANDLE, const char*, int, const char*, const char*, HANDLE, BOOL&);
typedef BOOL(CALLBACK* OnBeforeUnloadDialog_callback)(HANDLE, const char*, BOOL, HANDLE);
typedef void(CALLBACK* OnResetDialogState_callback)(HANDLE);
typedef void(CALLBACK* OnDialogClosed_callback)(HANDLE);
typedef void(CALLBACK* OnTakeFocus_callback)(HANDLE, BOOL);
typedef BOOL(CALLBACK* OnSetFocus_callback)(HANDLE, int);
typedef void(CALLBACK* OnGotFocus_callback)(HANDLE);
typedef void(CALLBACK* OnFindResult_callback)(HANDLE, int, int, HANDLE, int, BOOL);
typedef BOOL(CALLBACK* GetAuthCredentials_callback)(HANDLE, const char*, int, const char*, int, const char*, const char*, HANDLE);
typedef BOOL(CALLBACK* OnDragEnter_callback)(HANDLE, HANDLE, int);
typedef void(CALLBACK* OnDraggableRegionsChanged_callback)(HANDLE, HANDLE, HANDLE, int);
typedef void(CALLBACK* GetResourceResponseFilter_callback)(HANDLE, HANDLE, HANDLE, HANDLE, HANDLE); // 资源拦截入口 获取资源响应过滤器

// 渲染进程中执行
typedef void(CALLBACK* OnBrowserCreated_callback)(HANDLE, HANDLE);
typedef BOOL(CALLBACK* FBroApp_OnProcessMessageReceived_callback)(HANDLE, HANDLE, int, HANDLE); // 渲染进程收到消息

// 离屏渲染事件
typedef BOOL(CALLBACK* GetRootScreenRect_callback)(HANDLE, HANDLE);
typedef void(CALLBACK* GetViewRect_callback)(HANDLE, HANDLE);
typedef BOOL(CALLBACK* GetScreenPoint_callback)(HANDLE, int, int, int&, int&);
typedef BOOL(CALLBACK* GetScreenInfo_callback)(HANDLE, HANDLE);
typedef void(CALLBACK* OnPopupShow_callback)(HANDLE, BOOL);
typedef void(CALLBACK* OnPopupSize_callback)(HANDLE, HANDLE);
typedef void(CALLBACK* OnPaint_callback)(HANDLE, int, HANDLE, const void*, int, int);

typedef void(CALLBACK* OnAcceleratedPaint_callback)(HANDLE, int, HANDLE, void*);
typedef BOOL(CALLBACK* OnCursorChange_callback)(HANDLE, HANDLE, int, HANDLE);
typedef BOOL(CALLBACK* StartDragging_callback)(HANDLE, HANDLE, int, int, int);
typedef void(CALLBACK* UpdateDragCursor_callback)(HANDLE, int);
typedef void(CALLBACK* OnScrollOffsetChanged_callback)(HANDLE, double, double);
typedef void(CALLBACK* OnImeCompositionRangeChanged_callback)(HANDLE, HANDLE, HANDLE);
typedef void(CALLBACK* OnTextSelectionChanged_callback)(HANDLE, const char*, HANDLE);
typedef void(CALLBACK* OnVirtualKeyboardRequested_callback)(HANDLE, int);

// 资源处理器事件
typedef BOOL(CALLBACK* GetResourceHandler_callback)(HANDLE, HANDLE, HANDLE, int&);
typedef BOOL(CALLBACK* ResourceHandler_Open_callback)(int, HANDLE, BOOL&, BOOL&);
typedef BOOL(CALLBACK* ResourceHandler_ProcessRequest_callback)(int, HANDLE, BOOL&);
typedef void(CALLBACK* ResourceHandler_GetResponseHeaders_callback)(int, HANDLE, int64_t&, HANDLE);
typedef BOOL(CALLBACK* ResourceHandler_Skip_callback)(int, int64_t, int64_t&);
typedef BOOL(CALLBACK* ResourceHandler_Read_callback)(int, void*, int, int&);
typedef void(CALLBACK* ResourceHandler_Cancel_callback)(int);

/*******************************************************CefApp****************************************************************/
// 注册自定义方案
typedef void(CALLBACK* OnRegisterCustomSchemes_callback)(HANDLE, int);
/*******************************************************CefApp END****************************************************************/

/*****************************************CefBrowserProcessHandler****************************************************************/
// 子进程即将启动
typedef void(CALLBACK* OnBeforeChildProcessLaunch_callback)(HANDLE);
// 渲染进程即将创建
typedef void(CALLBACK* OnRenderProcessThreadCreated_callback)(HANDLE);
// 消息调度即将启动
typedef void(CALLBACK* OnScheduleMessagePumpWork_callback)(int64_t);
/*******************************************************CefBrowserProcessHandler END****************************************************************/

/*******************************************************CefRenderProcessHandler****************************************************************/
// 渲染进程即将创建
typedef void(CALLBACK* OnRenderThreadCreated_callback)(HANDLE);
// 初始化Web Kit
typedef void(CALLBACK* OnWebKitInitialized_callback)();
// 浏览器即将销毁
typedef void(CALLBACK* OnBrowserDestroyed_callback)(HANDLE);
// 即将创建环境
typedef void(CALLBACK* OnContextCreated_callback)(HANDLE, HANDLE, HANDLE);
// 即将释放环境
typedef void(CALLBACK* OnContextReleased_callback)(HANDLE, HANDLE, HANDLE);
// 即将捕获异常
typedef void(CALLBACK* OnUncaughtException_callback)(HANDLE, HANDLE, HANDLE, HANDLE, HANDLE);
// 焦点节点改变
typedef void(CALLBACK* OnFocusedNodeChanged_callback)(HANDLE, HANDLE, HANDLE);
//获取默认浏览器
typedef void(CALLBACK* OnGetDefaultClient_callback)(HANDLE, const char*, BOOL&, HANDLE);

typedef void(CALLBACK* OnRequestContextInitialized_Callback)(HANDLE);

// my add 20260512 插件创建成功的事件
typedef void(CALLBACK* OnCreateExtension_Callback)(HANDLE,const char*);

// my add 20260512 插件创建失败的事件
typedef void(CALLBACK* OnCreateExtensionError_Callback)(HANDLE, const char*, const char*, const char*);

// my add 20260512 添加插件
typedef void(CALLBACK* OnAddExtension_Callback)(HANDLE,const char*);

// my add 20260512 移除插件
typedef void(CALLBACK* OnRemoveExtension_Callback)(HANDLE,const char*);


typedef void(CALLBACK* Render_OnLoadingStateChange_callback)(HANDLE, BOOL, BOOL, BOOL);
typedef void(CALLBACK* Render_OnLoadStart_callback)(HANDLE, HANDLE, int);
typedef void(CALLBACK* Render_OnLoadEnd_callback)(HANDLE, HANDLE, int);
typedef void(CALLBACK* Render_OnLoadError_callback)(HANDLE, HANDLE, int, const char*, const char*);

/*********************插件事件*********************/
typedef void(CALLBACK* Extension_OnExtensionLoadFailedMessage_callback)(const char*, const char*);
typedef void(CALLBACK* Extension_OnExtensionLoadFailed_callback)(int);
typedef void(CALLBACK* Extension_OnExtensionLoaded_callback)(HANDLE);
typedef void(CALLBACK* Extension_OnExtensionUnloaded_callback)(HANDLE);
typedef BOOL(CALLBACK* Extension_OnBeforeBackgroundBrowser_callback)(HANDLE, const char*, HANDLE);
typedef BOOL(CALLBACK* Extension_OnBeforeBrowser_callback)(HANDLE, HANDLE, HANDLE, int, const char*, bool, HANDLE, HANDLE);
typedef HANDLE(CALLBACK* Extension_GetActiveBrowser_callback)(HANDLE, HANDLE, BOOL);
typedef BOOL(CALLBACK* Extension_CanAccessBrowser_callback)(HANDLE, HANDLE, BOOL, HANDLE);
typedef BOOL(CALLBACK* Extension_GetExtensionResource_callback)(HANDLE, HANDLE, const char*);

typedef void(CALLBACK* Extension_GetDefaultTabBrowser_callback)(HANDLE, HANDLE);

// 插件Client事件
typedef BOOL(CALLBACK* ExtensionClient_OnConsoleMessage_callback)(HANDLE, HANDLE, int, const char*, const char*, int);
typedef void(CALLBACK* ExtensionClient_OnAfterCreated_callback)(HANDLE, HANDLE);
typedef BOOL(CALLBACK* ExtensionClient_OnBeforePopup_callback)(HANDLE, HANDLE, HANDLE, const char*, const char*, int, BOOL, HANDLE, HANDLE, HANDLE, HANDLE, HANDLE, BOOL&);
typedef BOOL(CALLBACK* ExtensionClient_DoClose_callback)(HANDLE, HANDLE);
typedef void(CALLBACK* ExtensionClient_OnBeforeClose_callback)(HANDLE, HANDLE);

/**********************自定义渲染事件****************************/
typedef void(CALLBACK* Render_OnWebSocketCreate_callback)(HANDLE, HANDLE, HANDLE);
typedef void(CALLBACK* Render_OnWebSocketClose_callback)(HANDLE, HANDLE, HANDLE);
typedef void(CALLBACK* Render_OnWebSocketConnect_callback)(HANDLE, HANDLE, HANDLE, HANDLE&, HANDLE&);
typedef void(CALLBACK* Render_OnWebSocketError_callback)(HANDLE, HANDLE, HANDLE, const char*);
typedef BOOL(CALLBACK* Render_OnWebSocketSendText_callback)(HANDLE, HANDLE, HANDLE, HANDLE&);
typedef BOOL(CALLBACK* Render_OnWebSocketSendData_callback)(HANDLE, HANDLE, HANDLE, int, HANDLE&, int, int&);

typedef BOOL(CALLBACK* Render_OnWebSocketMessage_callback)(HANDLE, HANDLE, HANDLE, int, HANDLE&, int&);

/***********************自定义消息事件***************************/
typedef void(CALLBACK* Message_ReceiveRenderProcessMessage)(HANDLE, DWORD, const char*, const char*, int);
typedef void(CALLBACK* Message_ReceiveMainProcessMessage)(HANDLE, const char*, const char*, int);

/**************************20220825新内核增加******************/
typedef void(CALLBACK* OnDocumentAvailableInMainFrame_callback)(HANDLE);
typedef void(CALLBACK* OnMediaAccessChange_callback)(HANDLE, BOOL, BOOL);
typedef BOOL(CALLBACK* RunQuickMenu_callback)(HANDLE, HANDLE, int, int, int, int, int, HANDLE);
typedef BOOL(CALLBACK* OnQuickMenuCommand_callback)(HANDLE, HANDLE, int, int);
typedef void(CALLBACK* OnQuickMenuDismissed_callback)(HANDLE, HANDLE);
typedef BOOL(CALLBACK* CanDownload_callback)(HANDLE, const char*, const char*);
typedef BOOL(CALLBACK* GetAudioParameters_callback)(HANDLE, HANDLE /*CefAudioParameters*/);
typedef void(CALLBACK* OnAudioStreamStarted_callback)(HANDLE, HANDLE /*CefAudioParameters*/, int);
typedef void(CALLBACK* OnAudioStreamPacket_callback)(HANDLE, void*, int, int); // 这里long long传递给易不知道会不会被截断
typedef void(CALLBACK* OnAudioStreamStopped_callback)(HANDLE);
typedef void(CALLBACK* OnAudioStreamError_callback)(HANDLE, const char*);
typedef BOOL(CALLBACK* OnChromeCommand_callback)(HANDLE, int, int);
typedef void(CALLBACK* OnFrameCreated_callback)(HANDLE, HANDLE);
typedef void(CALLBACK* OnFrameAttached_callback)(HANDLE, HANDLE, BOOL);
typedef void(CALLBACK* OnFrameDetached_callback)(HANDLE, HANDLE);
typedef void(CALLBACK* OnMainFrameChanged_callback)(HANDLE, HANDLE, HANDLE);
typedef BOOL(CALLBACK* OnRequestMediaAccessPermission_callback)(HANDLE, HANDLE, const char*, int, HANDLE);
typedef BOOL(CALLBACK* OnShowPermissionPrompt_callback)(HANDLE, int, const char*, int, HANDLE);
typedef void(CALLBACK* OnDismissPermissionPrompt_callback)(HANDLE, int, int);

typedef void(CALLBACK* URLRequest_Start_callback)(int, HANDLE);
typedef void(CALLBACK* URLRequest_End_callback)(int);
typedef void(CALLBACK* URLRequest_OnRequestComplete_callback)(int, HANDLE);
typedef void(CALLBACK* URLRequest_OnUploadProgress_callback)(int, HANDLE, long, long);
typedef void(CALLBACK* URLRequest_OnDownloadProgress_callback)(int, HANDLE, long, long);
typedef void(CALLBACK* URLRequest_OnDownloadData_callback)(int, HANDLE, const void*, long);
typedef BOOL(CALLBACK* URLRequest_GetAuthCredentials_callback)(int, BOOL, const char*, int, const char*, const char*, HANDLE);

#endif



typedef struct E_ELEMENT_AT
{
	int x;
	int y;
} *PTELIB_ELEMENT_AT;

typedef struct E_KEYEVENT
{
	int type = 0;
	int modifiers = 0;
	int windows_key_code = 0;
	int native_key_code = 0;
	int is_system_key = 0;
	char h_character = 0;
	char character = 0;
	char h_unmodified_character = 0;
	char unmodified_character = 0;
	int focus_on_editable_field = 0;

} *PTELIB_KEYEVENT, * POINT_KEYEVENT;

typedef struct E_TOUCH_EVENT
{
	int type;
	int modifiers;
	int pointer_type;
	int id;
	float x;
	float y;
	float radius_x;
	float radius_y;
	float rotation_angle;
	float pressure;
} *PTELIB_TOUCH_EVENT;

typedef struct E_STRING_STRING
{
	char* first = NULL;
	char* second = NULL;

} *PTELIB_STRING_STRING;



// RequestContextSettings
typedef struct E_REQUSETCONTEXT_SET
{
	char* cache_path = NULL;
	BOOL persist_session_cookies;
	char* accept_language_list = NULL;

	char* cookieable_schemes_list = NULL;
	int cookieable_schemes_exclude_defaults;

} *POINT_REQUSETCONTEXT_SET;

typedef struct E_TIMEDATA
{
	int year;
	int month;
	int day;
	int hour;
	int minute;
	int second;
	int millisecond;
} *POINT_TIMEDATA;

typedef struct E_COOKIEDATA
{
	char* name = NULL;
	char* value = NULL;
	char* domain = NULL;
	char* path = NULL;
	BOOL httponly;
	BOOL has_expires;

	E_TIMEDATA expires_time;
	E_TIMEDATA last_access_time;

	int secure;
	int same_site;
	int priority;
} *POINT_COOKIEDATA;

typedef struct E_BYTEDATA
{
	HANDLE point;
	int size;

} *POINT_BYTEDATA;

typedef struct E_OSEVENT
{
	HWND hwnd;
	int message;
	WPARAM wParam;
	LPARAM lParam;
	int time;
	E_ELEMENT_AT point;
} *POINT_OSEVENT;

typedef struct E_DRAGGABLEREGION
{
	cef_rect_t rect;
	int draggable;
} *POINT_DRAGGABLEREGION;

typedef struct E_RECT
{
	int x;
	int y;
	int width;
	int height;
} *POINT_RECT;

typedef struct E_SCREENINFO
{
	float device_scale_factor;
	int depth;
	int depth_per_component;
	int is_monochrome;
	E_RECT rect;
	E_RECT available_rect;
} *POINT_SCREENINFO;

typedef struct E_CURSORINFO
{
	int x;
	int y;
	float image_scale_factor;
	void* buffer;
	int width;
	int height;
} *POINT_CURSORINFO;

typedef struct E_RANGE
{
	int from;
	int to;
} *POINT_RANGE;

typedef struct E_COMUNDERLINE
{
	E_RANGE range;
	int color;
	int background_color;
	int thick;
	int style;
} *POINT_COMUNDERLINE;

typedef struct E_MOUSEEVENT
{
	int x;
	int y;
	int modifiers;
} *POINT_MOUSEEVENT;

typedef struct E_SIZE {
	int width;
	int height;
} *POINT_SIZE;

typedef struct E_ACCELERATED_PAINT_INFO_COMMON {

	long timestamp;

	E_SIZE coded_size;

	E_RECT visible_rect;
	E_RECT content_rect;

	E_SIZE source_size;

	E_RECT capture_update_rect;
	E_RECT region_capture_rect;

	long capture_counter;
	int has_capture_update_rect;
	int has_region_capture_rect;
	int has_source_size;
	int has_capture_counter;

} *POINT_E_ACCELERATED_PAINT_INFO_COMMON;

typedef struct E_ACCELERATED_PAINT_INFO {
	HANDLE shared_texture_handle;
	int format;
	E_ACCELERATED_PAINT_INFO_COMMON extra;
} *POINT_ACCELERATED_PAINT_INFO;

typedef BOOL(CALLBACK* QUERY_FUNCTION)(HANDLE, HANDLE, const char*, HANDLE, int&, DWORD, int);

class FBroHsQueryHandler;

class FBroQueryHandler;
//class CefMessageRouterConfig;

typedef struct _Query_function
{
	// config.js_query_function = "cefQuerytest";
	// config.js_cancel_function = "cefQueryCanceltest";
	CefMessageRouterConfig config;
	CefRefPtr<FBroQueryHandler> handle = nullptr;

} Query_FUNCTION;

typedef std::list<Query_FUNCTION> ListQueryFunction;

typedef struct E_V8ACCESSOR
{
	HANDLE GetCallBack;
	HANDLE SetCallBack;
} *POINT_V8ACCESSOR;
// Interceptor
typedef struct E_V8INTERCEPTOR
{
	HANDLE GetNameCallBack;
	HANDLE SetNameCallBack;
	HANDLE GetIndexCallBack;
	HANDLE SetIndexCallBack;
} *POINT_V8INTERCEPTOR;

typedef struct E_URLParts
{
	char* spec = NULL;
	char* scheme = NULL;
	char* username = NULL;
	char* password = NULL;
	char* host = NULL;
	char* port = NULL;
	char* origin = NULL;
	char* path = NULL;
	char* query = NULL;
	char* fragment = NULL;
} *POINT_E_URLParts;

typedef struct E_AudioParameters
{
	int channel_layout;
	int sample_rate;
	int frames_per_buffer;
} *POINT_E_AudioParameters;


typedef struct
{
	void* onwebsocketcreate_ptr;
	void* onwebsocketclose_ptr;
	void* onwebsocketconnect_ptr;
	void* onwebsocketsend_ptr;
	void* onwebsocketmessage_ptr;
} VIP_WebSocket_data, * Pointer_VIP_WebSocket_data;

// 事件控制开关
typedef struct Event_Disable_Control
{
	BOOL disableGetAudioHandler = false;
	BOOL disableGetCommandHandler = false;
	BOOL disableGetContextMenuHandler = false;
	BOOL disableGetDialogHandler = false;
	BOOL disableGetDisplayHandler = false;
	BOOL disableGetDownloadHandler = false;
	BOOL disableGetDragHandler = false;
	BOOL disableGetFindHandler = false;
	BOOL disableGetFocusHandler = false;
	BOOL disableGetFrameHandler = false;
	BOOL disableGetPermissionHandler = false;
	BOOL disableGetJSDialogHandler = false;
	BOOL disableGetKeyboardHandler = false;
	BOOL disableGetLifeSpanHandler = false;
	BOOL disableGetLoadHandler = false;
	BOOL disableGetPrintHandler = false;
	BOOL disableGetRenderHandler = false;
	BOOL disableGetRequestHandler = false;
} *Pointer_Event_Disable_Control;


struct FBroPdfPrintSettings {

	/// <summary>
	/// Set to true (1) for landscape mode or false (0) for portrait mode.
	/// </summary>
	int landscape;

	/// <summary>
	/// Set to true (1) to print background graphics.
	/// </summary>
	int print_background;

	/// <summary>
	/// The percentage to scale the PDF by before printing (e.g. .5 is 50%).
	/// If this value is less than or equal to zero the default value of 1.0
	/// will be used.
	/// </summary>
	double scale;

	/// <summary>
	/// Output paper size in inches. If either of these values is less than or
	/// equal to zero then the default paper size (letter, 8.5 x 11 inches) will
	/// be used.
	/// </summary>
	double paper_width;
	double paper_height;

	/// <summary>
	/// Set to true (1) to prefer page size as defined by css. Defaults to false
	/// (0), in which case the content will be scaled to fit the paper size.
	/// </summary>
	int prefer_css_page_size;

	/// <summary>
	/// Margin type.
	/// </summary>
	int margin_type;

	/// <summary>
	/// Margins in inches. Only used if |margin_type| is set to
	/// PDF_PRINT_MARGIN_CUSTOM.
	/// </summary>
	double margin_top;
	double margin_right;
	double margin_bottom;
	double margin_left;

	/// <summary>
	/// Paper ranges to print, one based, e.g., '1-5, 8, 11-13'. Pages are printed
	/// in the document order, not in the order specified, and no more than once.
	/// Defaults to empty string, which implies the entire document is printed.
	/// The page numbers are quietly capped to actual page count of the document,
	/// and ranges beyond the end of the document are ignored. If this results in
	/// no pages to print, an error is reported. It is an error to specify a range
	/// with start greater than end.
	/// </summary>
	char* page_ranges;

	/// <summary>
	/// Set to true (1) to display the header and/or footer. Modify
	/// |header_template| and/or |footer_template| to customize the display.
	/// </summary>
	int display_header_footer;

	/// <summary>
	/// HTML template for the print header. Only displayed if
	/// |display_header_footer| is true (1). Should be valid HTML markup with
	/// the following classes used to inject printing values into them:
	///
	/// - date: formatted print date
	/// - title: document title
	/// - url: document location
	/// - pageNumber: current page number
	/// - totalPages: total pages in the document
	///
	/// </summary>
	char* header_template;

	/// <summary>
	/// HTML template for the print footer. Only displayed if
	/// |display_header_footer| is true (1). Uses the same format as
	/// |header_template|.
	/// </summary>
	char* footer_template;

	/// <summary>
	/// Set to true (1) to generate tagged (accessible) PDF.
	/// </summary>
	int generate_tagged_pdf;

	/// <summary>
	/// Set to true (1) to generate a document outline.
	/// </summary>
	int generate_document_outline;
};


/***************************************************************************/

enum REMOVE_DATA_MASK
{
	REMOVE_DATA_MASK_APPCACHE = 1 << 0,
	REMOVE_DATA_MASK_COOKIES = 1 << 1,
	REMOVE_DATA_MASK_FILE_SYSTEMS = 1 << 2,
	REMOVE_DATA_MASK_INDEXEDDB = 1 << 3,
	REMOVE_DATA_MASK_LOCAL_STORAGE = 1 << 4,
	REMOVE_DATA_MASK_SHADER_CACHE = 1 << 5,
	REMOVE_DATA_MASK_WEBSQL = 1 << 6,
	REMOVE_DATA_MASK_SERVICE_WORKERS = 1 << 7,
	REMOVE_DATA_MASK_CACHE_STORAGE = 1 << 8,
	REMOVE_DATA_MASK_PLUGIN_PRIVATE_DATA = 1 << 9,
	REMOVE_DATA_MASK_BACKGROUND_FETCH = 1 << 10,
	REMOVE_DATA_MASK_CONVERSIONS = 1 << 11,
	REMOVE_DATA_MASK_ALL = 0xFFFFFFFF
};

enum QUOTA_MANAGED_STORAGE
{
	QUOTA_MANAGED_STORAGE_MASK_TEMPORARY = 1 << 0,
	QUOTA_MANAGED_STORAGE_MASK_PERSISTENT = 1 << 1,
	QUOTA_MANAGED_STORAGE_MASK_SYNCABLE = 1 << 2,
	QUOTA_MANAGED_STORAGE_MASK_ALL = 0xFFFFFFFF
};

enum ProcessType
{
	BrowserProcess = 0,
	RendererProcess,
	GpuProcess,
	PpapiProcess,
	UtilityProcess,
	ZygoteProcess,
	OtherProcess,
};

#endif
