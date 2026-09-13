#pragma once
#ifndef FBROWSER_HSEVENT_H_
#define FBROWSER_HSEVENT_H_

#include "pch.h"
#include "FBroMiddleData.h"
//待处理#include "include\fbrowser\fbro_wssclient.h"
#include "FBroBaseEvent.h"

#include "FBroUseExtraData.h"

class FBroApp;
class FBroClient;
class FBroHsBroEvent;
class FBroHsEventBase;
class CefBrowser;

class FBroHsResourceHandler :public FBroBaseEvent
{
public:
	virtual void Start(int64_t flag) {

	}
	virtual void End(int64_t flag) {

	}
	virtual bool Open(int64_t flag, CefRefPtr<CefRequest> request,
		bool& handle_request,
		CefRefPtr<CefCallback> callback) {
		return false;
	};

	virtual bool ProcessRequest(int64_t flag, CefRefPtr<CefRequest> request,
		CefRefPtr<CefCallback> callback) {
		return false;
	};

	virtual void GetResponseHeaders(int64_t flag, CefRefPtr<CefResponse> response,
		int64_t& response_length,
		CefRefPtr<FBroString> redirectUrl) {
	};

	virtual bool Skip(int64_t flag, int64_t bytes_to_skip,
		int64_t& bytes_skipped,
		CefRefPtr<CefResourceSkipCallback> callback) {
		return false;
	};

	virtual bool Read(int64_t flag, void* data_out,
		int bytes_to_read,
		int& bytes_read,
		CefRefPtr<CefResourceReadCallback> callback) {
		return false;
	};
	virtual void Cancel(int64_t flag) {};
protected:
	IMPLEMENT_REFCOUNTING(FBroHsResourceHandler);
};


class FBroHsResponseFilter :public FBroBaseEvent {
public:

	virtual void Start(int64_t flag) {
	}
	virtual void End(int64_t flag) {
	}
	virtual bool InitFilter(int64_t flag) { return true; };

	virtual CefResponseFilter::FilterStatus Filter(int64_t flag, void* data_in,
		size_t data_in_size,
		size_t& data_in_read,
		void* data_out,
		size_t data_out_size,
		size_t& data_out_written) {
		if (data_in_size > data_out_size) {
			data_in_read = data_out_size;
			data_out_written = data_out_size;
			memcpy_s(data_out, data_out_size, data_in, data_out_size);
			return RESPONSE_FILTER_NEED_MORE_DATA;
		}
		else {
			data_in_read = data_in_size;
			data_out_written = data_in_size;
			memcpy_s(data_out, data_in_size, data_in, data_in_size);
			return RESPONSE_FILTER_DONE;
		}
	};

protected:
	IMPLEMENT_REFCOUNTING(FBroHsResponseFilter);
};

class FBroHsInitEvent :public FBroBaseEvent {
public:

	virtual void  OnBeforeCommandLineProcessing(
		const CefString& process_type,
		CefRefPtr<CefCommandLine> command_line) {
	};

	virtual void OnRegisterCustomSchemes(CefRawPtr<CefSchemeRegistrar> registrar) {};

	virtual void OnContextInitialized() {};
	virtual void OnBeforeChildProcessLaunch(CefRefPtr<CefCommandLine> command_line) {};

	virtual void OnScheduleMessagePumpWork(int64_t delay_ms) {};

	virtual void OnWebKitInitialized() {};
	virtual void OnBrowserCreated(CefRefPtr<CefBrowser> browser, CefRefPtr<CefDictionaryValue> extra_info) {};
	virtual void OnBrowserDestroyed(CefRefPtr<CefBrowser> browser) {};

	virtual void OnContextCreated(CefRefPtr<CefBrowser> browser,
		CefRefPtr<CefFrame> frame,
		CefRefPtr<CefV8Context> context) {
	};
	virtual void OnContextReleased(CefRefPtr<CefBrowser> browser,
		CefRefPtr<CefFrame> frame,
		CefRefPtr<CefV8Context> context) {
	};
	virtual void OnUncaughtException(CefRefPtr<CefBrowser> browser,
		CefRefPtr<CefFrame> frame,
		CefRefPtr<CefV8Context> context,
		CefRefPtr<CefV8Exception> exception,
		CefRefPtr<CefV8StackTrace> stackTrace) {
	};
	virtual void OnFocusedNodeChanged(CefRefPtr<CefBrowser> browser,
		CefRefPtr<CefFrame> frame,
		CefRefPtr<CefDOMNode> node) {
	};
	virtual bool OnProcessMessageReceived(CefRefPtr<CefBrowser> browser,
		CefRefPtr<CefFrame> frame,
		CefProcessId source_process,
		CefRefPtr<CefProcessMessage> message) {
		return false;
	};


	virtual void OnLoadingStateChange(CefRefPtr<CefBrowser> browser,
		bool isLoading,
		bool canGoBack,
		bool canGoForward) {
	};

	virtual void OnLoadStart(CefRefPtr<CefBrowser> browser,
		CefRefPtr<CefFrame> frame,
		CefLoadHandler::TransitionType transition_type) {
	};

	virtual void OnLoadEnd(CefRefPtr<CefBrowser> browser,
		CefRefPtr<CefFrame> frame,
		int httpStatusCode) {
	};

	virtual void OnLoadError(CefRefPtr<CefBrowser> browser,
		CefRefPtr<CefFrame> frame,
		CefLoadHandler::ErrorCode errorCode,
		const CefString& errorText,
		const CefString& failedUrl) {
	};

	virtual void  ReceiveMainProcessMessage(CefRefPtr<CefBrowser> browser,
		const CefString& name,
		char* message, int size) {
	};

	/*******************************************************CefRenderProcessHandler END****************************************************************/

	/***************************************************************VIP WSS拦截事件*********************************************************************/
	virtual void OnWebSocketClientCreate(CefRefPtr<CefBrowser> browser, CefRefPtr<CefFrame> frame, CefRefPtr<FBroDOMWssClient> websocket) {}

	virtual void OnWebSocketClientClose(CefRefPtr<CefBrowser> browser, CefRefPtr<CefFrame> frame, CefRefPtr<FBroDOMWssClient> websocket) {}

	virtual bool OnWebSocketClientMessage(CefRefPtr<CefBrowser> browser, CefRefPtr<CefFrame> frame, CefRefPtr<FBroDOMWssClient> websocket, int type, HANDLE& data, int& size) {
		return false;
	}

	virtual void OnWebSocketClientConnect(CefRefPtr<CefBrowser> browser, CefRefPtr<CefFrame> frame, CefRefPtr<FBroDOMWssClient> websocket, HANDLE& returl, HANDLE& protocols) {}

	virtual bool OnWebSocketClientSend(CefRefPtr<CefBrowser> browser, CefRefPtr<CefFrame> frame, CefRefPtr<FBroDOMWssClient> websocket, int type, HANDLE& retdata, int offsize, int& size) {
		return false;
	}
	/*****************************************************************************************************************************************************/

	//135增加的APP事件
	virtual void GetDefaultClient(CefRefPtr<CefBrowser> browsewr, const CefString& url, CefRefPtr<FBroUseExtraData> user_settings) {}
	///////////////////////

	virtual void OnRequestContextInitialized(CefRefPtr<CefRequestContext> request_context) {}

	// my add 20260512 插件创建成功的事件
	virtual void OnCreateExtension(CefRefPtr<CefRequestContext> requestContext,
		const CefString& extensionID) {
	}

	// my add 20260512 插件创建失败的事件
	virtual void OnCreateExtensionError(
		CefRefPtr<CefRequestContext> requestContext,
		const CefString& extensionID,
		const CefString& path,
		const CefString& error) {
	}

	// my add 20260512 添加插件
	virtual void OnAddExtension(CefRefPtr<CefRequestContext> requestContext,
		const CefString& extensionID) {
	}

	// my add 20260512 移除插件
	virtual void OnRemoveExtension(CefRefPtr<CefRequestContext> requestContext,
		const CefString& extensionID) {
	}


	//资源释放，用于某些申请了资源的数据释放，谁申请谁释放
	virtual void  ClearData(HANDLE data) {}


	virtual void FinishShutdown(BOOL& isshutdown) {}

	const int type = 1;
protected:
	IMPLEMENT_REFCOUNTING(FBroHsInitEvent);

};

class FBroHsBroEvent :public FBroBaseEvent
{
public:

	virtual bool OnProcessMessageReceived(CefRefPtr<CefBrowser> browser,
		CefRefPtr<CefFrame> frame,
		CefProcessId source_process,
		CefRefPtr<CefProcessMessage> message) {
		return false;
	};

	virtual bool OnBeforeBrowse(CefRefPtr<CefBrowser> browser,
		CefRefPtr<CefFrame> frame,
		CefRefPtr<CefRequest> request,
		bool user_gesture,
		bool is_redirect) {
		return false;
	};

	virtual bool OnOpenURLFromTab(CefRefPtr<CefBrowser> browser,
		CefRefPtr<CefFrame> frame,
		const CefString& target_url,
		CefRequestHandler::WindowOpenDisposition target_disposition,
		bool user_gesture) {
		return false;
	};

	virtual bool OnQuotaRequest(CefRefPtr<CefBrowser> browser,
		const CefString& origin_url,
		int64_t new_size,
		CefRefPtr<CefCallback> callback) {
		return false;
	};

	virtual bool OnCertificateError(CefRefPtr<CefBrowser> browser,
		cef_errorcode_t cert_error,
		const CefString& request_url,
		CefRefPtr<CefSSLInfo> ssl_info,
		CefRefPtr<CefCallback> callback) {
		return false;
	};

	virtual bool OnSelectClientCertificate(
		CefRefPtr<CefBrowser> browser,
		bool isProxy,
		const CefString& host,
		int port,
		CefRefPtr<FBroX509CertificateList> certificates,
		CefRefPtr<CefSelectClientCertificateCallback> callback) {
		return false;
	};

	virtual void OnPluginCrashed(CefRefPtr<CefBrowser> browser,
		const CefString& plugin_path) {
	};
	virtual void OnRenderViewReady(CefRefPtr<CefBrowser> browser) {};
	virtual void OnRenderProcessTerminated(CefRefPtr<CefBrowser> browser,
		CefRequestHandler::TerminationStatus status, int error_code,
		const CefString& error_string) {
	};


	virtual bool GetAuthCredentials(CefRefPtr<CefBrowser> browser,
		const CefString& origin_url,
		bool isProxy,
		const CefString& host,
		int port,
		const CefString& realm,
		const CefString& scheme,
		CefRefPtr<CefAuthCallback> callback) {
		return false;
	};
	virtual void OnDocumentAvailableInMainFrame(CefRefPtr<CefBrowser> browser) {};

	virtual void OnAfterCreated(CefRefPtr<CefBrowser> browser, CefRefPtr<CefDictionaryValue> extrainfo) {};
	virtual bool OnBeforePopup(CefRefPtr<CefBrowser> browser,
		CefRefPtr<CefFrame> frame,
		int popup_id,
		const CefString& target_url,
		const CefString& target_frame_name,
		CefLifeSpanHandler::WindowOpenDisposition target_disposition,
		bool user_gesture,
		const CefPopupFeatures& popupFeatures,
		CefWindowInfo& windowInfo,
		CefBrowserSettings& settings,
		bool* no_javascript_access,
		CefRefPtr<FBroUseExtraData> user_settings) {
		return false;
	};

	virtual void OnBeforePopupAborted(CefRefPtr<CefBrowser> browser, int popup_id) {};

	virtual void OnBeforeDevToolsPopup(CefRefPtr<CefBrowser> browser,
		CefWindowInfo& windowInfo,
		CefBrowserSettings& settings,
		bool* use_default_window,
		CefRefPtr<FBroUseExtraData> user_settings) {
	};


	virtual bool DoClose(CefRefPtr<CefBrowser> browser) { return false; };
	virtual void OnBeforeClose(CefRefPtr<CefBrowser> browser) {};

	virtual void OnAddressChange(CefRefPtr<CefBrowser> browser,
		CefRefPtr<CefFrame> frame,
		const CefString& url) {
	};
	virtual void OnTitleChange(CefRefPtr<CefBrowser> browser,
		const CefString& title) {
	};
	virtual void OnFaviconURLChange(CefRefPtr<CefBrowser> browser,
		CefRefPtr<CefListValue> icon_urls) {
	};
	virtual void OnFullscreenModeChange(CefRefPtr<CefBrowser> browser,
		bool fullscreen) {
	};
	virtual bool OnTooltip(CefRefPtr<CefBrowser> browser,
		CefRefPtr<FBroString> text) {
		return false;
	};
	virtual void OnStatusMessage(CefRefPtr<CefBrowser> browser,
		const CefString& value) {
	};
	virtual bool OnConsoleMessage(CefRefPtr<CefBrowser> browser,
		cef_log_severity_t level,
		const CefString& message,
		const CefString& source,
		int line) {
		return false;
	};


	virtual bool OnAutoResize(CefRefPtr<CefBrowser> browser,
		const CefSize& new_size) {
		return false;
	};
	virtual void OnLoadingProgressChange(CefRefPtr<CefBrowser> browser,
		double progress) {
	};


	virtual bool OnCursorChange(CefRefPtr<CefBrowser> browser,
		CefCursorHandle cursor,
		cef_cursor_type_t type,
		const CefCursorInfo& custom_cursor_info) {
		return false;
	};

	virtual void OnMediaAccessChange(CefRefPtr<CefBrowser> browser,
		bool has_video_access,
		bool has_audio_access) {
	};

	//即将加载资源
	virtual CefResourceRequestHandler::ReturnValue OnBeforeResourceLoad(
		CefRefPtr<CefBrowser> browser,
		CefRefPtr<CefFrame> frame,
		CefRefPtr<CefRequest> request,
		CefRefPtr<CefCallback> callback) {
		return RV_CONTINUE;
	};   //RV_CONTINUE

	virtual CefRefPtr<CefResourceHandler> GetResourceHandler(
		CefRefPtr<CefBrowser> browser,
		CefRefPtr<CefFrame> frame,
		CefRefPtr<CefRequest> request) {
		return nullptr;
	};


	virtual void OnResourceRedirect(CefRefPtr<CefBrowser> browser,
		CefRefPtr<CefFrame> frame,
		CefRefPtr<CefRequest> request,
		CefRefPtr<CefResponse> response,
		CefRefPtr<FBroString> new_url) {
	};

	virtual bool OnResourceResponse(CefRefPtr<CefBrowser> browser,
		CefRefPtr<CefFrame> frame,
		CefRefPtr<CefRequest> request,
		CefRefPtr<CefResponse> response) {
		return false;
	};

	virtual CefRefPtr<CefResponseFilter> GetResourceResponseFilter(
		CefRefPtr<CefBrowser> browser,
		CefRefPtr<CefFrame> frame,
		CefRefPtr<CefRequest> request,
		CefRefPtr<CefResponse> response) {
		return nullptr;
	};


	//资源加载完毕
	virtual void OnResourceLoadComplete(CefRefPtr<CefBrowser> browser,
		CefRefPtr<CefFrame> frame,
		CefRefPtr<CefRequest> request,
		CefRefPtr<CefResponse> response,
		CefResourceRequestHandler::URLRequestStatus status,
		int64_t received_content_length) {
	};


	virtual void OnProtocolExecution(CefRefPtr<CefBrowser> browser,
		CefRefPtr<CefFrame> frame,
		CefRefPtr<CefRequest> request,
		bool& allow_os_execution) {
	};

	virtual void OnLoadingStateChange(CefRefPtr<CefBrowser> browser,
		bool isLoading,
		bool canGoBack,
		bool canGoForward) {
	};

	virtual void OnLoadStart(CefRefPtr<CefBrowser> browser,
		CefRefPtr<CefFrame> frame,
		CefLoadHandler::TransitionType transition_type) {
	};

	virtual void OnLoadEnd(CefRefPtr<CefBrowser> browser,
		CefRefPtr<CefFrame> frame,
		int httpStatusCode) {
	};

	virtual void OnLoadError(CefRefPtr<CefBrowser> browser,
		CefRefPtr<CefFrame> frame,
		CefLoadHandler::ErrorCode errorCode,
		const CefString& errorText,
		const CefString& failedUrl) {
	};

	virtual void OnBeforeContextMenu(CefRefPtr<CefBrowser> browser,
		CefRefPtr<CefFrame> frame,
		CefRefPtr<CefContextMenuParams> params,
		CefRefPtr<CefMenuModel> model) {
	};

	virtual bool RunContextMenu(CefRefPtr<CefBrowser> browser,
		CefRefPtr<CefFrame> frame,
		CefRefPtr<CefContextMenuParams> params,
		CefRefPtr<CefMenuModel> model,
		CefRefPtr<CefRunContextMenuCallback> callback) {
		return false;
	};

	virtual bool OnContextMenuCommand(CefRefPtr<CefBrowser> browser,
		CefRefPtr<CefFrame> frame,
		CefRefPtr<CefContextMenuParams> params,
		int command_id,
		CefContextMenuHandler::EventFlags event_flags) {
		return false;
	};

	virtual void OnContextMenuDismissed(CefRefPtr<CefBrowser> browser,
		CefRefPtr<CefFrame> frame) {
	};

	virtual bool RunQuickMenu(CefRefPtr<CefBrowser> browser,
		CefRefPtr<CefFrame> frame,
		PTELIB_ELEMENT_AT location,
		POINT_SIZE size,
		int edit_state_flags,
		CefRefPtr<CefRunQuickMenuCallback> callback) {
		return false;
	}

	virtual bool OnQuickMenuCommand(CefRefPtr<CefBrowser> browser,
		CefRefPtr<CefFrame> frame,
		int command_id,
		int event_flags) {
		return false;
	}

	virtual void OnQuickMenuDismissed(CefRefPtr<CefBrowser> browser,
		CefRefPtr<CefFrame> frame) {
	}

	virtual bool CanDownload(CefRefPtr<CefBrowser> browser,
		const CefString& url,
		const CefString& request_method) {
		return true;
	}

	virtual bool OnBeforeDownload(
		CefRefPtr<CefBrowser> browser,
		CefRefPtr<CefDownloadItem> download_item,
		const CefString& suggested_name,
		CefRefPtr<CefBeforeDownloadCallback> callback) {
		return false;
	};

	virtual void OnDownloadUpdated(
		CefRefPtr<CefBrowser> browser,
		CefRefPtr<CefDownloadItem> download_item,
		CefRefPtr<CefDownloadItemCallback> callback) {
	};

	virtual bool OnPreKeyEvent(CefRefPtr<CefBrowser> browser,
		PTELIB_KEYEVENT event,
		POINT_OSEVENT os_event,
		bool* is_keyboard_shortcut) {
		return false;
	};

	virtual bool OnKeyEvent(CefRefPtr<CefBrowser> browser,
		PTELIB_KEYEVENT event,
		POINT_OSEVENT os_event) {
		return false;
	};

	virtual bool OnFileDialog(CefRefPtr<CefBrowser> browser,
		CefDialogHandler::FileDialogMode mode,
		const CefString& title,
		const CefString& default_file_path,
		CefRefPtr<FBroCefStringList> accept_filters,
		CefRefPtr<FBroCefStringList> accept_extensions,
		CefRefPtr<FBroCefStringList> accept_descriptions,
		CefRefPtr<CefFileDialogCallback> callback) {
		return false;
	};


	virtual bool OnJSDialog(CefRefPtr<CefBrowser> browser,
		const CefString& origin_url,
		CefJSDialogHandler::JSDialogType dialog_type,
		const CefString& message_text,
		const CefString& default_prompt_text,
		CefRefPtr<CefJSDialogCallback> callback,
		bool& suppress_message) {
		return false;
	};

	virtual bool OnBeforeUnloadDialog(CefRefPtr<CefBrowser> browser,
		const CefString& message_text,
		bool is_reload,
		CefRefPtr<CefJSDialogCallback> callback) {
		return false;
	};

	virtual void OnResetDialogState(CefRefPtr<CefBrowser> browser) {};

	virtual void OnDialogClosed(CefRefPtr<CefBrowser> browser) {};

	virtual void OnTakeFocus(CefRefPtr<CefBrowser> browser, bool next) {};

	virtual bool OnSetFocus(CefRefPtr<CefBrowser> browser, CefFocusHandler::FocusSource source) { return false; };

	virtual void OnGotFocus(CefRefPtr<CefBrowser> browser) {};

	virtual void OnFindResult(CefRefPtr<CefBrowser> browser,
		int identifier,
		int count,
		POINT_RECT selectionRect,
		int activeMatchOrdinal,
		bool finalUpdate) {
	};

	virtual bool OnDragEnter(CefRefPtr<CefBrowser> browser,
		CefRefPtr<CefDragData> dragData,
		CefDragHandler::DragOperationsMask mask) {
		return false;
	};

	virtual void OnDraggableRegionsChanged(
		CefRefPtr<CefBrowser> browser,
		CefRefPtr<CefFrame> frame,
		CefRefPtr<FBroDraggableRegion> regions) {
	};

	virtual void ReceiveRenderProcessMessage(CefRefPtr<CefBrowser> browser,
		int64_t processid,
		const CefString& name,
		char* message, int size) {
	};

	/*****************************CefAudioHandler***********************************/
	virtual bool GetAudioParameters(CefRefPtr<CefBrowser> browser,
		CefAudioParameters& params) {
		return false;
	}

	virtual void OnAudioStreamStarted(CefRefPtr<CefBrowser> browser,
		const CefAudioParameters& params,
		int channels) {
	}

	virtual void OnAudioStreamPacket(CefRefPtr<CefBrowser> browser,
		const float** data,
		int frames,
		int64_t pts) {
	};

	virtual void OnAudioStreamStopped(CefRefPtr<CefBrowser> browser) {};

	virtual void OnAudioStreamError(CefRefPtr<CefBrowser> browser,
		const CefString& message) {
	};
	/*********************************************************************************/


	/**********************************  CefCommandHandler**********************************/
	virtual bool OnChromeCommand(CefRefPtr<CefBrowser> browser,
		int command_id,
		cef_window_open_disposition_t disposition) {
		return false;
	}
	/**********************************	 CefCommandHandler END**********************************/


	/**********************************	 CefFrameHandler**********************************/
	virtual void OnFrameCreated(CefRefPtr<CefBrowser> browser,
		CefRefPtr<CefFrame> frame) {
	}

	virtual void OnFrameAttached(CefRefPtr<CefBrowser> browser,
		CefRefPtr<CefFrame> frame,
		bool reattached) {
	}

	virtual void OnFrameDetached(CefRefPtr<CefBrowser> browser,
		CefRefPtr<CefFrame> frame) {
	}

	virtual void OnMainFrameChanged(CefRefPtr<CefBrowser> browser,
		CefRefPtr<CefFrame> old_frame,
		CefRefPtr<CefFrame> new_frame) {
	}
	/**********************************	 CefFrameHandler END**********************************/


	/**********************************	 CefPermissionHandler**********************************/
	virtual bool OnRequestMediaAccessPermission(
		CefRefPtr<CefBrowser> browser,
		CefRefPtr<CefFrame> frame,
		const CefString& requesting_origin,
		uint32_t requested_permissions,
		CefRefPtr<CefMediaAccessCallback> callback) {
		return false;
	}

	virtual bool OnShowPermissionPrompt(
		CefRefPtr<CefBrowser> browser,
		uint64_t prompt_id,
		const CefString& requesting_origin,
		uint32_t requested_permissions,
		CefRefPtr<CefPermissionPromptCallback> callback) {
		return false;
	}

	virtual void OnDismissPermissionPrompt(
		CefRefPtr<CefBrowser> browser,
		uint64_t prompt_id,
		cef_permission_request_result_t result) {
	}
	/**********************************	 CefPermissionHandler END**********************************/


public:
	//离屏渲染相关
	virtual bool GetRootScreenRect(CefRefPtr<CefBrowser> browser, CefRect& rect) { return false; };
	virtual void GetViewRect(CefRefPtr<CefBrowser> browser, CefRect& rect) {};
	virtual bool GetScreenPoint(CefRefPtr<CefBrowser> browser, int viewX, int viewY, int& screenX, int& screenY) {
		return false;
	};
	virtual bool GetScreenInfo(CefRefPtr<CefBrowser> browser, CefScreenInfo& screen_info) {
		return false;
	};
	virtual void OnPopupShow(CefRefPtr<CefBrowser> browser, bool show) {};
	virtual void OnPopupSize(CefRefPtr<CefBrowser> browser, const CefRect& rect) {};
	virtual void OnPaint(CefRefPtr<CefBrowser> browser, CefRenderHandler::PaintElementType type, CefRefPtr<FBroRectValueList> dirtyRects, const void* buffer, int width, int height) {};

	virtual void OnAcceleratedPaint(CefRefPtr<CefBrowser> browser, CefRenderHandler::PaintElementType type, CefRefPtr<FBroRectValueList> dirtyRects, const CefAcceleratedPaintInfo& info) {};


	virtual bool StartDragging(CefRefPtr<CefBrowser> browser, CefRefPtr<CefDragData> drag_data, CefRenderHandler::DragOperationsMask allowed_ops, int x, int y) {
		return false;
	};

	virtual void UpdateDragCursor(CefRefPtr<CefBrowser> browser,
		CefRenderHandler::DragOperation operation) {
	};

	virtual void OnScrollOffsetChanged(CefRefPtr<CefBrowser> browser, double x, double y) {};

	virtual void OnImeCompositionRangeChanged(CefRefPtr<CefBrowser> browser, const CefRange& selected_range, CefRefPtr<FBroRectValueList> character_bounds) {};

	virtual void OnTextSelectionChanged(CefRefPtr<CefBrowser> browser, const CefString& selected_text, const CefRange& selected_range) {};

	virtual void OnVirtualKeyboardRequested(CefRefPtr<CefBrowser> browser, CefRenderHandler::TextInputMode input_mode) {};

	const int type = 1;
protected:
	IMPLEMENT_REFCOUNTING(FBroHsBroEvent);
};

class FBroHsDownloadImageCallback :public FBroBaseEvent {

public:

	virtual void OnDownloadImageFinished(const CefString& image_url,
		int http_status_code,
		CefRefPtr<CefImage> image) {
	};
protected:
	IMPLEMENT_REFCOUNTING(FBroHsDownloadImageCallback);
};

class FBroHsFileDialogCallback :public FBroBaseEvent
{
public:

	virtual void FBroHs_OnFileDialogDismissed(
		/*int selected_accept_filter,新内核取消*/
		const wchar_t* file_paths) {
	};
protected:
	IMPLEMENT_REFCOUNTING(FBroHsFileDialogCallback);
};

class FBroHsPdfPrintCallback :public FBroBaseEvent {
public:

	virtual void OnPdfPrintFinished(const CefString& path, bool ok) {};
protected:
	IMPLEMENT_REFCOUNTING(FBroHsPdfPrintCallback);
};

class FBroHsStringVisitor :public FBroBaseEvent {
public:

	virtual void Visit(const CefString& string) {};
protected:
	IMPLEMENT_REFCOUNTING(FBroHsStringVisitor);
};


class FBroHsJsCallback :public FBroBaseEvent {
public:

	virtual void Callback(CefRefPtr<CefListValue> pListValue) {};
protected:
	IMPLEMENT_REFCOUNTING(FBroHsJsCallback);
};

class FBroHsDOMVisitor :public FBroBaseEvent
{
public:

public:
	virtual void Visit(CefRefPtr<CefDOMDocument> document) {
	};
protected:
	IMPLEMENT_REFCOUNTING(FBroHsDOMVisitor);
};

class FBroHsTask :public FBroBaseEvent {
public:
	virtual void Execute() {};

protected:
	IMPLEMENT_REFCOUNTING(FBroHsTask);
};

class FBroHsCookieVisitor :public FBroBaseEvent {
public:
	virtual void Start() {};
	virtual void End() {};
	virtual bool Visit(POINT_COOKIEDATA cookie, int count, int total, bool& deleteCookie) { return false; };

protected:
	IMPLEMENT_REFCOUNTING(FBroHsCookieVisitor);
};

class FBroHsQueryHandler :public FBroBaseEvent
{

public:
	virtual bool OnQuery(CefRefPtr<CefBrowser> browser,
		CefRefPtr<CefFrame> frame,
		int64_t query_id,
		const CefString& request,
		bool persistent,
		CefRefPtr<CefMessageRouterBrowserSide::Handler::Callback> callback) {
		return false;
	};

	virtual void OnQueryCanceled(CefRefPtr<CefBrowser> browser,
		CefRefPtr<CefFrame> frame,
		int64_t query_id) {
	};

protected:
	IMPLEMENT_REFCOUNTING(FBroHsQueryHandler);
};

class FBroHsV8Handler :public FBroBaseEvent
{
public:
	virtual void Start(int64_t flag) {};
	virtual void End(int64_t flag) {};
	virtual bool Execute(int64_t flag, const CefString& name,
		CefRefPtr<CefV8Value> object,
		CefRefPtr<FBroV8ValueList> arguments,
		CefRefPtr<CefV8Value>& retval,
		CefRefPtr<FBroString> exception) {
		return false;
	}

protected:
	IMPLEMENT_REFCOUNTING(FBroHsV8Handler);

};

class FBroHsV8Accessor :public FBroBaseEvent
{
public:
	virtual void Start(int64_t flag) {};
	virtual void End(int64_t flag) {};
	virtual bool Get(int64_t flag, const CefString& name,
		const CefRefPtr<CefV8Value> object,
		CefRefPtr<CefV8Value>& retval,
		CefRefPtr<FBroString> exception) {
		return false;
	};

	virtual bool Set(int64_t flag, const CefString& name,
		const CefRefPtr<CefV8Value> object,
		const CefRefPtr<CefV8Value> value,
		CefRefPtr<FBroString>  exception) {
		return false;
	};

protected:
	IMPLEMENT_REFCOUNTING(FBroHsV8Accessor);

};

class FBroHsV8Interceptor :public FBroBaseEvent
{
public:
	virtual void Start(int64_t flag) {};
	virtual void End(int64_t flag) {};
	virtual bool Get(int64_t flag, const CefString& name,
		const CefRefPtr<CefV8Value> object,
		CefRefPtr<CefV8Value>& retval,
		CefRefPtr<FBroString> exception) {
		return false;
	};

	virtual bool Get(int64_t flag, int index,
		const CefRefPtr<CefV8Value> object,
		CefRefPtr<CefV8Value>& retval,
		CefRefPtr<FBroString> exception) {
		return false;
	};


	virtual bool Set(int64_t flag, const CefString& name,
		const CefRefPtr<CefV8Value> object,
		const CefRefPtr<CefV8Value> value,
		CefRefPtr<FBroString> exception) {
		return false;
	};


	virtual bool Set(int64_t flag, int index,
		const CefRefPtr<CefV8Value> object,
		const CefRefPtr<CefV8Value> value,
		CefRefPtr<FBroString> exception) {
		return false;
	};

protected:
	IMPLEMENT_REFCOUNTING(FBroHsV8Interceptor);

};

class FBroHsServerHandle :public FBroBaseEvent
{
public:

	virtual void OnServerCreated(CefRefPtr<CefServer> server) {
	};

	virtual void OnServerDestroyed(CefRefPtr<CefServer> server) {
	};

	virtual void OnClientConnected(CefRefPtr<CefServer> server,
		int connection_id) {
	};

	virtual void OnClientDisconnected(CefRefPtr<CefServer> server,
		int connection_id) {
	};

	virtual void OnHttpRequest(CefRefPtr<CefServer> server,
		int connection_id,
		const CefString& client_address,
		CefRefPtr<CefRequest> request) {
	};

	virtual void OnWebSocketRequest(CefRefPtr<CefServer> server,
		int connection_id,
		const CefString& client_address,
		CefRefPtr<CefRequest> request,
		CefRefPtr<CefCallback> callback) {
	};


	virtual void OnWebSocketConnected(CefRefPtr<CefServer> server,
		int connection_id) {
	};


	virtual void OnWebSocketMessage(CefRefPtr<CefServer> server,
		int connection_id,
		const void* data,
		size_t data_size) {
	};

protected:
	IMPLEMENT_REFCOUNTING(FBroHsServerHandle);

};


class FBroHsClearCacheCallback :public FBroBaseEvent {
public:

	virtual void DoFinish(bool success) {};
protected:
	IMPLEMENT_REFCOUNTING(FBroHsClearCacheCallback);
};


class FBroHsURLRequestClient :public FBroBaseEvent
{

public:
	virtual void Start(int64_t flag, CefRefPtr<CefURLRequest> request) {};
	virtual void End(int64_t flag) {};

	virtual void OnRequestComplete(int64_t flag, CefRefPtr<CefURLRequest> request) {}

	virtual void OnUploadProgress(int64_t flag, CefRefPtr<CefURLRequest> request,
		int64_t current,
		int64_t total) {
	}

	virtual void OnDownloadProgress(int64_t flag, CefRefPtr<CefURLRequest> request,
		int64_t current,
		int64_t total) {
	}

	virtual void OnDownloadData(int64_t flag, CefRefPtr<CefURLRequest> request,
		const void* data,
		size_t data_length) {
	}

	virtual bool GetAuthCredentials(int64_t flag, bool isProxy,
		const CefString& host,
		int port,
		const CefString& realm,
		const CefString& scheme,
		CefRefPtr<CefAuthCallback> callback) {
		return false;
	}
protected:
	IMPLEMENT_REFCOUNTING(FBroHsURLRequestClient);
};


#endif