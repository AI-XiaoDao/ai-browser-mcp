#pragma once
#ifndef FBROWSER_CLIENT_H_
#define FBROWSER_CLIENT_H_
#include "FBroHsBaseEvent.h"


extern std::atomic_int browser_count_;

typedef std::list <CefRefPtr<CefMessageRouterBrowserSide>> MessageRouterBrowserSidelist; //browser_side_router_

class FBroString;
class CefBrowser;
class FBroVIPControl;

class FBroClientBase :public FBroHsEventModel<FBroHsBroEvent> {
public:
	FBroClientBase(CefRefPtr<FBroHsBroEvent> hsevent) :FBroHsEventModel(hsevent) {
		is_close_ = false;
	}
	~FBroClientBase() {
		is_close_ = true;
	};

public:
	std::atomic<bool> is_close_ = true;
};

class FBroClient :public CefClient,
	public CefLifeSpanHandler,
	public CefRequestHandler,
	public FBroClientBase {
public:

	//FBroClient();

	FBroClient(CefRefPtr<FBroHsBroEvent> hsbroevent, Event_Disable_Control* eventDisableControl,
		int fbrowserID, bool is_devclient = false, bool enable_outside_event = true);

	FBroClient(CefRefPtr<FBroHsBroEvent> hsbroevent, const Event_Disable_Control& eventDisableControl,
		int fbrowserID, bool is_devclient = false, bool enable_outside_event = true);

	//FBroClient(FBroHsBroEvent* hsbroevent, Pointer_Event_Disable_Control eventDisableControl,
	//	int fbrowserID, bool is_devclient = false, bool enable_outside_event = true);

	~FBroClient();

private:
	void Init(const Event_Disable_Control& eventDisableControl, bool is_devclient, bool enable_outside_event);

	std::atomic_bool is_clear_ = false;

	void Clear();
public:

	CefRefPtr<CefAudioHandler> GetAudioHandler() override;
	CefRefPtr<CefCommandHandler> GetCommandHandler() override;
	CefRefPtr<CefContextMenuHandler> GetContextMenuHandler() override;
	CefRefPtr<CefDialogHandler> GetDialogHandler() override;
	CefRefPtr<CefDisplayHandler> GetDisplayHandler() override;
	CefRefPtr<CefDownloadHandler> GetDownloadHandler() override;
	CefRefPtr<CefDragHandler> GetDragHandler() override;
	CefRefPtr<CefFindHandler> GetFindHandler() override;
	CefRefPtr<CefFocusHandler> GetFocusHandler() override;
	CefRefPtr<CefFrameHandler> GetFrameHandler() override;
	CefRefPtr<CefPermissionHandler> GetPermissionHandler() override;
	CefRefPtr<CefJSDialogHandler> GetJSDialogHandler() override;
	CefRefPtr<CefKeyboardHandler> GetKeyboardHandler() override;
	CefRefPtr<CefLifeSpanHandler> GetLifeSpanHandler() override;
	CefRefPtr<CefLoadHandler> GetLoadHandler() override;
	CefRefPtr<CefRenderHandler> GetRenderHandler() override;
	CefRefPtr<CefRequestHandler> GetRequestHandler() override;

	/*******************************CefClient***************************************/
	bool OnProcessMessageReceived(CefRefPtr<CefBrowser> browser,
		CefRefPtr<CefFrame> frame,
		CefProcessId source_process,
		CefRefPtr<CefProcessMessage> message)override;
	/***************************************************************************************/

	class ResourceRequestHandler :public CefResourceRequestHandler, public FBroClientBase {
	public:
		ResourceRequestHandler(CefRefPtr<FBroHsBroEvent> hsbroevent) :
			FBroClientBase(hsbroevent) {
		}

	public:
		//待添加
		CefRefPtr<CefCookieAccessFilter> GetCookieAccessFilter(
			CefRefPtr<CefBrowser> browser,
			CefRefPtr<CefFrame> frame,
			CefRefPtr<CefRequest> request)override {
			return nullptr;
		}

		//即将加载资源
		ReturnValue OnBeforeResourceLoad(
			CefRefPtr<CefBrowser> browser,
			CefRefPtr<CefFrame> frame,
			CefRefPtr<CefRequest> request,
			CefRefPtr<CefCallback> callback)  override;

		CefRefPtr<CefResourceHandler> GetResourceHandler(
			CefRefPtr<CefBrowser> browser,
			CefRefPtr<CefFrame> frame,
			CefRefPtr<CefRequest> request)override;


		void OnResourceRedirect(CefRefPtr<CefBrowser> browser,
			CefRefPtr<CefFrame> frame,
			CefRefPtr<CefRequest> request,
			CefRefPtr<CefResponse> response,
			CefString& new_url) override;

		bool OnResourceResponse(CefRefPtr<CefBrowser> browser,
			CefRefPtr<CefFrame> frame,
			CefRefPtr<CefRequest> request,
			CefRefPtr<CefResponse> response) override;

		//资源拦截入口 获取资源响应过滤器
		CefRefPtr<CefResponseFilter> GetResourceResponseFilter(
			CefRefPtr<CefBrowser> browser,
			CefRefPtr<CefFrame> frame,
			CefRefPtr<CefRequest> request,
			CefRefPtr<CefResponse> response) override;


		//资源加载完毕
		void OnResourceLoadComplete(CefRefPtr<CefBrowser> browser,
			CefRefPtr<CefFrame> frame,
			CefRefPtr<CefRequest> request,
			CefRefPtr<CefResponse> response,
			URLRequestStatus status,
			int64_t received_content_length) override;


		void OnProtocolExecution(CefRefPtr<CefBrowser> browser,
			CefRefPtr<CefFrame> frame,
			CefRefPtr<CefRequest> request,
			bool& allow_os_execution) override;
	protected:
		IMPLEMENT_REFCOUNTING(ResourceRequestHandler);
	};


	/*******************************CefRequestHandler 有一个未添加回调***************************************/

	bool OnBeforeBrowse(CefRefPtr<CefBrowser> browser,
		CefRefPtr<CefFrame> frame,
		CefRefPtr<CefRequest> request,
		bool user_gesture,
		bool is_redirect) override;

	bool OnOpenURLFromTab(CefRefPtr<CefBrowser> browser,
		CefRefPtr<CefFrame> frame,
		const CefString& target_url,
		CefRequestHandler::WindowOpenDisposition target_disposition,
		bool user_gesture) override;

	CefRefPtr<CefResourceRequestHandler> GetResourceRequestHandler(
		CefRefPtr<CefBrowser> browser,
		CefRefPtr<CefFrame> frame,
		CefRefPtr<CefRequest> request,
		bool is_navigation,
		bool is_download,
		const CefString& request_initiator,
		bool& disable_default_handling) override;

	bool GetAuthCredentials(CefRefPtr<CefBrowser> browser,
		const CefString& origin_url,
		bool isProxy,
		const CefString& host,
		int port,
		const CefString& realm,
		const CefString& scheme,
		CefRefPtr<CefAuthCallback> callback) override;

	//证书错误
	bool OnCertificateError(CefRefPtr<CefBrowser> browser,
		cef_errorcode_t cert_error,
		const CefString& request_url,
		CefRefPtr<CefSSLInfo> ssl_info,
		CefRefPtr<CefCallback> callback) override;

	bool OnSelectClientCertificate(
		CefRefPtr<CefBrowser> browser,
		bool isProxy,
		const CefString& host,
		int port,
		const X509CertificateList& certificates,
		CefRefPtr<CefSelectClientCertificateCallback> callback) override;



	void OnRenderViewReady(CefRefPtr<CefBrowser> browser) override;

	//待添加 
	bool OnRenderProcessUnresponsive(
		CefRefPtr<CefBrowser> browser,
		CefRefPtr<CefUnresponsiveProcessCallback> callback)override {
		return false;
	}

	//待添加 
	void OnRenderProcessResponsive(CefRefPtr<CefBrowser> browser)override {}

	//134添加参数已处理
	void OnRenderProcessTerminated(CefRefPtr<CefBrowser> browser,
		TerminationStatus status, int error_code,
		const CefString& error_string)override;


	void OnDocumentAvailableInMainFrame(CefRefPtr<CefBrowser> browser) override;

	/*****************************CefRequestHandler**********************************************************/


	/*******************************CefLifeSpanHandler已完成***************************************/

	bool OnBeforePopup(CefRefPtr<CefBrowser> browser,
		CefRefPtr<CefFrame> frame,
		int popup_id,
		const CefString& target_url,
		const CefString& target_frame_name,
		CefLifeSpanHandler::WindowOpenDisposition target_disposition,
		bool user_gesture,
		const CefPopupFeatures& popupFeatures,
		CefWindowInfo& windowInfo,
		CefRefPtr<CefClient>& client,
		CefBrowserSettings& settings,
		CefRefPtr<CefDictionaryValue>& extra_info,
		bool* no_javascript_access) override;

	//打开新窗口被取消
	void OnBeforePopupAborted(CefRefPtr<CefBrowser> browser,
		int popup_id) override;

	//即将打开开发者弹窗
	void OnBeforeDevToolsPopup(CefRefPtr<CefBrowser> browser,
		CefWindowInfo& windowInfo,
		CefRefPtr<CefClient>& client,
		CefBrowserSettings& settings,
		CefRefPtr<CefDictionaryValue>& extra_info,
		bool* use_default_window) override;

	void OnAfterCreatedDis(CefRefPtr<CefBrowser> browser);

	void OnAfterCreated(CefRefPtr<CefBrowser> browser)  override;


	bool DoClose(CefRefPtr<CefBrowser> browser)  override;
	void OnBeforeClose(CefRefPtr<CefBrowser> browser)  override;
	/***********************************CefLifeSpanHandler END****************************************************/


	/*******************************CefDisplayHandler已完成***************************************/
	class DisplayHandler :public CefDisplayHandler, public FBroClientBase {
	public:
		DisplayHandler(CefRefPtr<FBroHsBroEvent> hsbroevent) :FBroClientBase(hsbroevent) {}

		void OnAddressChange(CefRefPtr<CefBrowser> browser,
			CefRefPtr<CefFrame> frame,
			const CefString& url) override;
		void OnTitleChange(CefRefPtr<CefBrowser> browser,
			const CefString& title) override;
		void OnFaviconURLChange(CefRefPtr<CefBrowser> browser,
			const std::vector<CefString>& icon_urls) override;
		void OnFullscreenModeChange(CefRefPtr<CefBrowser> browser,
			bool fullscreen) override;
		bool OnTooltip(CefRefPtr<CefBrowser> browser,
			CefString& text) override;
		void OnStatusMessage(CefRefPtr<CefBrowser> browser,
			const CefString& value) override;
		bool OnConsoleMessage(CefRefPtr<CefBrowser> browser,
			cef_log_severity_t level,
			const CefString& message,
			const CefString& source,
			int line)override;

		bool OnAutoResize(CefRefPtr<CefBrowser> browser,
			const CefSize& new_size) override;
		void OnLoadingProgressChange(CefRefPtr<CefBrowser> browser,
			double progress) override;

		//当浏览器的光标改变时调用。如果|type|是CT_CUSTOM，那么|custom_cursor_info|将被填充自定义游标信息。
		bool OnCursorChange(CefRefPtr<CefBrowser> browser,
			CefCursorHandle cursor,
			cef_cursor_type_t type,
			const CefCursorInfo& custom_cursor_info) override;

		void OnMediaAccessChange(CefRefPtr<CefBrowser> browser,
			bool has_video_access,
			bool has_audio_access) override;
	protected:
		IMPLEMENT_REFCOUNTING(DisplayHandler);
	};
	/**********************************CefDisplayHandler END************************************/


	/**********************************CefLoadHandler 已完成************************************/
	class LoadHandler :public CefLoadHandler, public FBroClientBase {
	public:
		LoadHandler(CefRefPtr<FBroHsBroEvent> hsbroevent) :FBroClientBase(hsbroevent) {}

		void OnLoadingStateChange(CefRefPtr<CefBrowser> browser,
			bool isLoading,
			bool canGoBack,
			bool canGoForward) override;

		void OnLoadStart(CefRefPtr<CefBrowser> browser,
			CefRefPtr<CefFrame> frame,
			TransitionType transition_type)  override;

		void OnLoadEnd(CefRefPtr<CefBrowser> browser,
			CefRefPtr<CefFrame> frame,
			int httpStatusCode) override;

		void OnLoadError(CefRefPtr<CefBrowser> browser,
			CefRefPtr<CefFrame> frame,
			ErrorCode errorCode,
			const CefString& errorText,
			const CefString& failedUrl)  override;

	protected:
		IMPLEMENT_REFCOUNTING(LoadHandler);
	};
	/**********************************CefLoadHandler END************************************/


	/**********************************CefContextMenuHandler 已完成************************************/
	class ContextMenuHandler :public CefContextMenuHandler, public FBroClientBase {
	public:
		ContextMenuHandler(CefRefPtr<FBroHsBroEvent> hsbroevent) :FBroClientBase(hsbroevent) {}

		void OnBeforeContextMenu(CefRefPtr<CefBrowser> browser,
			CefRefPtr<CefFrame> frame,
			CefRefPtr<CefContextMenuParams> params,
			CefRefPtr<CefMenuModel> model) override;

		bool RunContextMenu(CefRefPtr<CefBrowser> browser,
			CefRefPtr<CefFrame> frame,
			CefRefPtr<CefContextMenuParams> params,
			CefRefPtr<CefMenuModel> model,
			CefRefPtr<CefRunContextMenuCallback> callback) override;

		bool OnContextMenuCommand(CefRefPtr<CefBrowser> browser,
			CefRefPtr<CefFrame> frame,
			CefRefPtr<CefContextMenuParams> params,
			int command_id,
			EventFlags event_flags) override;

		void OnContextMenuDismissed(CefRefPtr<CefBrowser> browser,
			CefRefPtr<CefFrame> frame) override;

		bool RunQuickMenu(CefRefPtr<CefBrowser> browser,
			CefRefPtr<CefFrame> frame,
			const CefPoint& location,
			const CefSize& size,
			QuickMenuEditStateFlags edit_state_flags,
			CefRefPtr<CefRunQuickMenuCallback> callback)override;

		bool OnQuickMenuCommand(CefRefPtr<CefBrowser> browser,
			CefRefPtr<CefFrame> frame,
			int command_id,
			EventFlags event_flags) override;

		void OnQuickMenuDismissed(CefRefPtr<CefBrowser> browser,
			CefRefPtr<CefFrame> frame) override;
	protected:
		IMPLEMENT_REFCOUNTING(ContextMenuHandler);
	};

	/**********************************CefContextMenuHandler END************************************/


	/**********************************CefDownloadHandler 已完成************************************/
	class DownloadHandler :public CefDownloadHandler, public FBroClientBase {
	public:
		DownloadHandler(CefRefPtr<FBroHsBroEvent> hsbroevent) :FBroClientBase(hsbroevent) {}

		bool CanDownload(CefRefPtr<CefBrowser> browser,
			const CefString& url,
			const CefString& request_method) override;

		//134已处理添加返回值
		bool OnBeforeDownload(
			CefRefPtr<CefBrowser> browser,
			CefRefPtr<CefDownloadItem> download_item,
			const CefString& suggested_name,
			CefRefPtr<CefBeforeDownloadCallback> callback) override;

		void OnDownloadUpdated(
			CefRefPtr<CefBrowser> browser,
			CefRefPtr<CefDownloadItem> download_item,
			CefRefPtr<CefDownloadItemCallback> callback) override;
	protected:
		IMPLEMENT_REFCOUNTING(DownloadHandler);
	};

	/**********************************CefDownloadHandler END************************************/

	/**********************************CefKeyboardHandler 已完成************************************/
	class KeyboardHandler :public CefKeyboardHandler, public FBroClientBase {
	public:
		KeyboardHandler(CefRefPtr<FBroHsBroEvent> hsbroevent) :FBroClientBase(hsbroevent) {}

		bool OnPreKeyEvent(CefRefPtr<CefBrowser> browser,
			const CefKeyEvent& event,
			CefEventHandle os_event,
			bool* is_keyboard_shortcut) override;

		bool OnKeyEvent(CefRefPtr<CefBrowser> browser,
			const CefKeyEvent& event,
			CefEventHandle os_event) override;

	protected:
		IMPLEMENT_REFCOUNTING(KeyboardHandler);
	};

	/**********************************CefKeyboardHandler END************************************/



	/**********************************CefDialogHandler 已完成************************************/
	class DialogHandler :public CefDialogHandler, public FBroClientBase {
	public:
		DialogHandler(CefRefPtr<FBroHsBroEvent> hsbroevent) :FBroClientBase(hsbroevent) {}

		//待添加参数 
		bool OnFileDialog(CefRefPtr<CefBrowser> browser,
			FileDialogMode mode,
			const CefString& title,
			const CefString& default_file_path,
			const std::vector<CefString>& accept_filters,
			const std::vector<CefString>& accept_extensions,
			const std::vector<CefString>& accept_descriptions,
			CefRefPtr<CefFileDialogCallback> callback) override;

	protected:
		IMPLEMENT_REFCOUNTING(DialogHandler);
	};

	/**********************************CefDialogHandler END************************************/

	/**********************************CefJSDialogHandler 已完成************************************/
	class JSDialogHandler :public CefJSDialogHandler, public FBroClientBase {
	public:
		JSDialogHandler(CefRefPtr<FBroHsBroEvent> hsbroevent) :FBroClientBase(hsbroevent) {}

		bool OnJSDialog(CefRefPtr<CefBrowser> browser,
			const CefString& origin_url,
			JSDialogType dialog_type,
			const CefString& message_text,
			const CefString& default_prompt_text,
			CefRefPtr<CefJSDialogCallback> callback,
			bool& suppress_message) override;

		bool OnBeforeUnloadDialog(CefRefPtr<CefBrowser> browser,
			const CefString& message_text,
			bool is_reload,
			CefRefPtr<CefJSDialogCallback> callback) override;

		void OnResetDialogState(CefRefPtr<CefBrowser> browser) override;

		void OnDialogClosed(CefRefPtr<CefBrowser> browser) override;

	protected:
		IMPLEMENT_REFCOUNTING(JSDialogHandler);
	};
	/**********************************CefJSDialogHandler END************************************/


	/**********************************CefFocusHandler 已完成**********************************/
	class FocusHandler :public CefFocusHandler, public FBroClientBase {
	public:
		FocusHandler(CefRefPtr<FBroHsBroEvent> hsbroevent) :FBroClientBase(hsbroevent) {}

		void OnTakeFocus(CefRefPtr<CefBrowser> browser, bool next) override;

		bool OnSetFocus(CefRefPtr<CefBrowser> browser, FocusSource source) override;

		void OnGotFocus(CefRefPtr<CefBrowser> browser) override;

	protected:
		IMPLEMENT_REFCOUNTING(FocusHandler);
	};

	/**********************************CefFocusHandler END**********************************/

	/**********************************CefFindHandler 已完成**********************************/
	class FindHandler :public CefFindHandler, public FBroClientBase {
	public:
		FindHandler(CefRefPtr<FBroHsBroEvent> hsbroevent) :FBroClientBase(hsbroevent) {}

		void OnFindResult(CefRefPtr<CefBrowser> browser,
			int identifier,
			int count,
			const CefRect& selectionRect,
			int activeMatchOrdinal,
			bool finalUpdate) override;

	protected:
		IMPLEMENT_REFCOUNTING(FindHandler);
	};

	/**********************************CefFindHandler END**********************************/

	/**********************************CefDragHandler 已完成**********************************/
	class DragHandler :public CefDragHandler, public FBroClientBase {
	public:
		DragHandler(CefRefPtr<FBroHsBroEvent> hsbroevent) :FBroClientBase(hsbroevent) {}

		bool OnDragEnter(CefRefPtr<CefBrowser> browser,
			CefRefPtr<CefDragData> dragData,
			DragOperationsMask mask)  override;

		void OnDraggableRegionsChanged(
			CefRefPtr<CefBrowser> browser,
			CefRefPtr<CefFrame> frame,
			const std::vector<CefDraggableRegion>& regions) override;

	protected:
		IMPLEMENT_REFCOUNTING(DragHandler);
	};


	/**********************************CefDragHandler END**********************************/

	 /*****************************CefAudioHandler 待完善***********************************/
	class AudioHandler :public CefAudioHandler, public FBroClientBase {
	public:
		AudioHandler(CefRefPtr<FBroHsBroEvent> hsbroevent) :FBroClientBase(hsbroevent) {}

		bool GetAudioParameters(CefRefPtr<CefBrowser> browser,
			CefAudioParameters& params) override;

		void OnAudioStreamStarted(CefRefPtr<CefBrowser> browser,
			const CefAudioParameters& params,
			int channels) override;

		void OnAudioStreamPacket(CefRefPtr<CefBrowser> browser,
			const float** data,
			int frames,
			int64_t pts) override;

		void OnAudioStreamStopped(CefRefPtr<CefBrowser> browser) override;

		void OnAudioStreamError(CefRefPtr<CefBrowser> browser,
			const CefString& message) override;

	protected:
		IMPLEMENT_REFCOUNTING(AudioHandler);
	};
	/*********************************************************************************/



	/**********************************  CefCommandHandler 待处理**********************************/
	class CommandHandler :public CefCommandHandler, public FBroClientBase {
	public:
		CommandHandler(CefRefPtr<FBroHsBroEvent> hsbroevent) :FBroClientBase(hsbroevent) {}

		bool OnChromeCommand(CefRefPtr<CefBrowser> browser,
			int command_id,
			cef_window_open_disposition_t disposition) override;

	protected:
		IMPLEMENT_REFCOUNTING(CommandHandler);
	};
	/**********************************	 CefCommandHandler END**********************************/



	/**********************************	 CefFrameHandler 待处理**********************************/
	class FrameHandler :public CefFrameHandler, public FBroClientBase {
	public:
		FrameHandler(CefRefPtr<FBroHsBroEvent> hsbroevent) :FBroClientBase(hsbroevent) {}

		void OnFrameCreated(CefRefPtr<CefBrowser> browser,
			CefRefPtr<CefFrame> frame)override;

		//待添加
		void OnFrameDestroyed(CefRefPtr<CefBrowser> browser,
			CefRefPtr<CefFrame> frame) override {
		}

		void OnFrameAttached(CefRefPtr<CefBrowser> browser,
			CefRefPtr<CefFrame> frame,
			bool reattached);

		void OnFrameDetached(CefRefPtr<CefBrowser> browser,
			CefRefPtr<CefFrame> frame) override;

		void OnMainFrameChanged(CefRefPtr<CefBrowser> browser,
			CefRefPtr<CefFrame> old_frame,
			CefRefPtr<CefFrame> new_frame) override;
	protected:
		IMPLEMENT_REFCOUNTING(FrameHandler);
	};

	/**********************************	 CefFrameHandler END**********************************/


	/**********************************	 CefPermissionHandler 待处理**********************************/
	class PermissionHandler :public CefPermissionHandler, public FBroClientBase {
	public:
		PermissionHandler(CefRefPtr<FBroHsBroEvent> hsbroevent) :FBroClientBase(hsbroevent) {}

		bool OnRequestMediaAccessPermission(
			CefRefPtr<CefBrowser> browser,
			CefRefPtr<CefFrame> frame,
			const CefString& requesting_origin,
			uint32_t requested_permissions,
			CefRefPtr<CefMediaAccessCallback> callback) override;

		bool OnShowPermissionPrompt(
			CefRefPtr<CefBrowser> browser,
			uint64_t prompt_id,
			const CefString& requesting_origin,
			uint32_t requested_permissions,
			CefRefPtr<CefPermissionPromptCallback> callback) override;

		void OnDismissPermissionPrompt(
			CefRefPtr<CefBrowser> browser,
			uint64_t prompt_id,
			cef_permission_request_result_t result) override;

	protected:
		IMPLEMENT_REFCOUNTING(PermissionHandler);
	};


	/**********************************	 CefPermissionHandler END**********************************/

	/// <summary>
	/// 离屏渲染相关处理类
	/// </summary>
	class RenderHandler :public CefRenderHandler, public FBroClientBase //,public CefAccessibilityHandler
	{
	public:
		RenderHandler(CefRefPtr<FBroHsBroEvent> hsbroevent) :FBroClientBase(hsbroevent) {}

	public:
		//CefRefPtr<CefAccessibilityHandler> GetAccessibilityHandler() override {
		//    return this;
		//}

		//void OnAccessibilityTreeChange(CefRefPtr<CefValue> value) override {
		//};

		//void OnAccessibilityLocationChange(CefRefPtr<CefValue> value) override {
		//} ;

		bool GetRootScreenRect(CefRefPtr<CefBrowser> browser, CefRect& rect) override;

		void GetViewRect(CefRefPtr<CefBrowser> browser, CefRect& rect) override;

		bool GetScreenPoint(CefRefPtr<CefBrowser> browser,
			int viewX,
			int viewY,
			int& screenX,
			int& screenY)override;

		bool GetScreenInfo(CefRefPtr<CefBrowser> browser,
			CefScreenInfo& screen_info)override;

		void OnPopupShow(CefRefPtr<CefBrowser> browser, bool show) override;

		void OnPopupSize(CefRefPtr<CefBrowser> browser, const CefRect& rect) override;

		void OnPaint(CefRefPtr<CefBrowser> browser,
			PaintElementType type,
			const RectList& dirtyRects,
			const void* buffer,
			int width,
			int height) override;

		////////////////////////////////////////////////////////////////////////
		//最后一个参数改为const CefAcceleratedPaintInfo& info
		void OnAcceleratedPaint(CefRefPtr<CefBrowser> browser,
			PaintElementType type,
			const RectList& dirtyRects,
			const CefAcceleratedPaintInfo& info) override;


		bool StartDragging(CefRefPtr<CefBrowser> browser,
			CefRefPtr<CefDragData> drag_data,
			DragOperationsMask allowed_ops,
			int x,
			int y)override;

		void UpdateDragCursor(CefRefPtr<CefBrowser> browser,
			DragOperation operation) override;


		void OnScrollOffsetChanged(CefRefPtr<CefBrowser> browser,
			double x,
			double y) override;


		void OnImeCompositionRangeChanged(CefRefPtr<CefBrowser> browser,
			const CefRange& selected_range,
			const RectList& character_bounds) override;


		void OnTextSelectionChanged(CefRefPtr<CefBrowser> browser,
			const CefString& selected_text,
			const CefRange& selected_range) override;


		void OnVirtualKeyboardRequested(CefRefPtr<CefBrowser> browser,
			TextInputMode input_mode) override;

	protected:
		IMPLEMENT_REFCOUNTING(RenderHandler);
	};


public:

	MessageRouterBrowserSidelist browser_side_router_;

	////浏览器创建的时候设置的标识，最终用于保存到浏览器清单中
	//CefString user_flag_ = "";

	////用于浏览器创建的时候设置的额外数据
	//CefRefPtr<CefDictionaryValue> extrainfo_ = nullptr;

	void SetInitWindowInfo(const CefWindowInfo& window_info) {


		if (window_info.bounds.height == 0 && window_info.bounds.width == 0 && window_info.bounds.x == 0 && window_info.bounds.y == 0)
			return;

		if (window_info.bounds.height == INT_MIN && window_info.bounds.width == INT_MIN && window_info.bounds.x == INT_MIN && window_info.bounds.y == INT_MIN)
			return;

		init_window_info_.havSet = true;
		init_window_info_.window_info = window_info;


	}

private:
	struct InitWindowInfo
	{
		bool havSet = false;
		CefWindowInfo window_info;
	};

	//主要谷歌模式后初始化窗口未知没效果，就在这里传递一下，创建成功后在设置
	InitWindowInfo init_window_info_;

private:

	CefRefPtr<CefRenderHandler> m_renderhandler = nullptr;



	Event_Disable_Control eventDisableControl_;

	//同事件创建个数,如果是谷歌UI通过点击+号添加的浏览器会使用第一个浏览器相同的事件，所以这里就有多个
	std::atomic<int> creat_count_ = 0;

	//是否触发外部事件
	bool enable_outside_event_ = true;


	CefRefPtr<AudioHandler> audio_handler_ = nullptr;
	CefRefPtr<CommandHandler> command_handle_ = nullptr;
	CefRefPtr<ContextMenuHandler> context_menu_handle_ = nullptr;
	CefRefPtr<DialogHandler> dialog_handle_ = nullptr;
	CefRefPtr<DisplayHandler> display_handle_ = nullptr;
	CefRefPtr<DownloadHandler> download_handler_ = nullptr;
	CefRefPtr<DragHandler> drag_handler_ = nullptr;
	CefRefPtr<FindHandler> find_handler_ = nullptr;
	CefRefPtr<FocusHandler> focus_handler_ = nullptr;
	CefRefPtr<FrameHandler> frame_handle_ = nullptr;
	CefRefPtr<PermissionHandler> permission_handle_ = nullptr;
	CefRefPtr<JSDialogHandler> js_dialog_handle_ = nullptr;
	CefRefPtr<KeyboardHandler> keyboard_handle_ = nullptr;
	//CefRefPtr<LifeSpanHandler> life_span_handler_ = nullptr;
	CefRefPtr<LoadHandler> load_handler_ = nullptr;
	CefRefPtr<RenderHandler> render_handler_ = nullptr;
	//CefRefPtr<RequestHandler> request_handler_ = nullptr;
	CefRefPtr<ResourceRequestHandler> resource_request_handler_ = nullptr;

public:

	CefRefPtr<ResourceRequestHandler> GetCreatResourceRequestHandler() {
		return resource_request_handler_;
	};

	bool is_devclient_ = false;

	//父浏览器ID，如果为0则没有父浏览器
	const int fbrowserID_;


//private:
//	CefRefPtr<FBroVIPControl> fbro_vipcontrol_ = nullptr;
//
//public:
//	void SetFBroVIPControl(CefRefPtr<FBroVIPControl>);
//	CefRefPtr<FBroVIPControl> GetFBroVIPControl();


protected:
	DISALLOW_COPY_AND_ASSIGN(FBroClient);
	IMPLEMENT_REFCOUNTING(FBroClient);

};

//DLLEXPORT void TEXPORTS FBroClient_SetFBroVIPControl(CefRefPtr<CefBrowser> browser, CefRefPtr<FBroVIPControl>);
//DLLEXPORT CefRefPtr<FBroVIPControl> TEXPORTS FBroClient_GetFBroVIPControl(CefRefPtr<CefBrowser> browser);

DLLEXPORT CefRefPtr<CefClient> TEXPORTS FBroClient_Creat(CefRefPtr<CefBrowser> browser,
	CefRefPtr<FBroHsBroEvent> hsbroevent, const Event_Disable_Control& eventContrl);

#endif