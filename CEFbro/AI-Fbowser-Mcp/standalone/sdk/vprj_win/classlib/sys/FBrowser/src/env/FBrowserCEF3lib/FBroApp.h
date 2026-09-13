#pragma once
#ifndef FBROWSER_APP_H_
#define FBROWSER_APP_H_

#include "FBroHsBaseEvent.h"

class FBroHsInitEvent;

typedef  std::list<CefRefPtr<CefMessageRouterRendererSide>>  CefMessageRouterRendererSidelist;


extern int randport;
extern bool is_singleprocess;
extern CefMessageRouterRendererSidelist renderer_side_router_;

class FBroApp :public CefApp
	//,public CefResourceBundleHandler
	, public CefBrowserProcessHandler
	, public CefRenderProcessHandler
	, public CefLoadHandler
	, public CefRequestContextHandler
	, public FBroHsEventModel<FBroHsInitEvent>
{

public:
	FBroApp(CefRefPtr<FBroHsInitEvent> initevent);
	FBroApp(FBroHsInitEvent* initevent);

	~FBroApp();

	// Determine the process type based on command-line arguments.
	static ProcessType GetProcessType(CefRefPtr<CefCommandLine> command_line);


	//virtual CefRefPtr<CefResourceBundleHandler> GetResourceBundleHandler() override { return this; };

	virtual CefRefPtr<CefBrowserProcessHandler> GetBrowserProcessHandler() override;
	virtual CefRefPtr<CefRenderProcessHandler> GetRenderProcessHandler() override;

	//渲染进程中使用
	virtual CefRefPtr<CefLoadHandler> GetLoadHandler() override;

	//重载事件
protected:

	/*******************************************************CefApp 待完善****************************************************************/
	virtual void OnBeforeCommandLineProcessing(
		const CefString& process_type,
		CefRefPtr<CefCommandLine> command_line) override;

	//注册自定义方案
	virtual void OnRegisterCustomSchemes(CefRawPtr<CefSchemeRegistrar> registrar)override;
	/*******************************************************CefApp END****************************************************************/

	/*****************************************CefBrowserProcessHandler 待完善****************************************************************/
	virtual void OnContextInitialized() override; //初始化完毕
	virtual void OnBeforeChildProcessLaunch(CefRefPtr<CefCommandLine> command_line) override;

	virtual void OnScheduleMessagePumpWork(int64_t delay_ms) override;

	//单例消息，没有启用单例模式所以暂时不用，待处理
	virtual bool OnAlreadyRunningAppRelaunch(
		CefRefPtr<CefCommandLine> command_line,
		const CefString& current_directory) override {
		return false;
	}

	virtual CefRefPtr<CefClient> GetDefaultClient(CefRefPtr<CefBrowser> browser, const CefString& url, CefRefPtr<CefDictionaryValue>& extra_info) override;


	virtual CefRefPtr<CefRequestContextHandler>
		GetDefaultRequestContextHandler() override {
		return this;
	}


	virtual void OnRequestContextInitialized(
		CefRefPtr<CefRequestContext> request_context) override ;

	virtual CefRefPtr<CefResourceRequestHandler> GetResourceRequestHandler(
		CefRefPtr<CefBrowser> browser,
		CefRefPtr<CefFrame> frame,
		CefRefPtr<CefRequest> request,
		bool is_navigation,
		bool is_download,
		const CefString& request_initiator,
		bool& disable_default_handling) override;


	// my add 20260512 插件创建成功的事件
	virtual void OnCreateExtension(CefRefPtr<CefRequestContext> requestContext,
		const CefString& extensionID) override;

	// my add 20260512 插件创建失败的事件
	virtual void OnCreateExtensionError(
		CefRefPtr<CefRequestContext> requestContext,
		const CefString& extensionID,
		const CefString& path,
		const CefString& error) override;

	// my add 20260512 添加插件
	virtual void OnAddExtension(CefRefPtr<CefRequestContext> requestContext,
		const CefString& extensionID)override;

	// my add 20260512 移除插件
	virtual void OnRemoveExtension(CefRefPtr<CefRequestContext> requestContext,
		const CefString& extensionID) override;

	/*******************************************************CefBrowserProcessHandler END****************************************************************/

	/*******************************************************CefRenderProcessHandler 待完善****************************************************************/
	virtual void OnWebKitInitialized() override;
	virtual void OnBrowserCreated(CefRefPtr<CefBrowser> browser, CefRefPtr<CefDictionaryValue> extra_info) override;
	virtual void OnBrowserDestroyed(CefRefPtr<CefBrowser> browser) override;

	virtual void OnContextCreated(CefRefPtr<CefBrowser> browser,
		CefRefPtr<CefFrame> frame,
		CefRefPtr<CefV8Context> context) override;
	virtual void OnContextReleased(CefRefPtr<CefBrowser> browser,
		CefRefPtr<CefFrame> frame,
		CefRefPtr<CefV8Context> context) override;
	virtual void OnUncaughtException(CefRefPtr<CefBrowser> browser,
		CefRefPtr<CefFrame> frame,
		CefRefPtr<CefV8Context> context,
		CefRefPtr<CefV8Exception> exception,
		CefRefPtr<CefV8StackTrace> stackTrace) override;
	virtual void OnFocusedNodeChanged(CefRefPtr<CefBrowser> browser,
		CefRefPtr<CefFrame> frame,
		CefRefPtr<CefDOMNode> node) override;
	virtual bool OnProcessMessageReceived(CefRefPtr<CefBrowser> browser,
		CefRefPtr<CefFrame> frame,
		CefProcessId source_process,
		CefRefPtr<CefProcessMessage> message) override;


	virtual void OnLoadingStateChange(CefRefPtr<CefBrowser> browser,
		bool isLoading,
		bool canGoBack,
		bool canGoForward) override;

	virtual void OnLoadStart(CefRefPtr<CefBrowser> browser,
		CefRefPtr<CefFrame> frame,
		TransitionType transition_type) override;

	virtual void OnLoadEnd(CefRefPtr<CefBrowser> browser,
		CefRefPtr<CefFrame> frame,
		int httpStatusCode) override;

	virtual void OnLoadError(CefRefPtr<CefBrowser> browser,
		CefRefPtr<CefFrame> frame,
		ErrorCode errorCode,
		const CefString& errorText,
		const CefString& failedUrl) override;



	/*******************************************************CefRenderProcessHandler END****************************************************************/

	
	// websocket相关回调

  //即将创建wss
	virtual void OnWebSocketCreate(CefRefPtr<CefBrowser> browser,
		CefRefPtr<CefFrame> frame,
		CefRefPtr<FBroDOMWssClient> wssClient) override;
	//即将关闭wss
	virtual void OnWebSocketClose(CefRefPtr<CefBrowser> browser,
		CefRefPtr<CefFrame> frame,
		CefRefPtr<FBroDOMWssClient> wssClient) override;
	//即将连接wss
	virtual void OnWebSocketConnect(CefRefPtr<CefBrowser> browser,
		CefRefPtr<CefFrame> frame,
		CefRefPtr<FBroDOMWssClient> wssClient,
		const char* url,
		const char* protocols,
		void*& returl,
		void*& retprotocols) override;
	// wss即将发送数据
	virtual bool OnWebSocketSend(CefRefPtr<CefBrowser> browser,
		CefRefPtr<CefFrame> frame,
		CefRefPtr<FBroDOMWssClient> wssClient,
		int type,
		const char* data,
		int size,
		void*& retdata,
		int offsize,
		int& retsize) override;
	// wss即将收到数据
	virtual bool OnWebSocketMessage(CefRefPtr<CefBrowser> browser,
		CefRefPtr<CefFrame> frame,
		CefRefPtr<FBroDOMWssClient> wssClient,
		int type,
		const char* data,
		int size,
		void*& retdata,
		int& retsize) override;
	virtual void ClearWebSocketChangeData(void* data, int size) override;

public:
	//自定义事件关闭完成
	void FinishShutdown(BOOL isclose);


private:
	IMPLEMENT_REFCOUNTING(FBroApp);
	DISALLOW_COPY_AND_ASSIGN(FBroApp);

};

DLLEXPORT void TEXPORTS FBroHsInitEventDestroy();


#endif
