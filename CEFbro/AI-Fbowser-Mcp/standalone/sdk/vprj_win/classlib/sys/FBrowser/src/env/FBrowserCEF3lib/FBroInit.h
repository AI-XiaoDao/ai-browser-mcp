#pragma once
#ifndef FBROWSER_INIT_H_
#define FBROWSER_INIT_H_

class FBroApp;
class FBroHsResourceHandler;
class FBroResourceHandler;
class FBroHsInitEvent;
class CPP_ThreadTimer;

typedef struct JSFunNameHandle {
	HANDLE nameMap = NULL;
	LPVOID nameMen = NULL;//数据指针
}*Point_JSFunNameHandle;

typedef struct InitBaseSetShareData {
	bool enable_high_DPI = false;
	int high_DPI_Type = 0;
	int is_live_mainprocess_cycle_time = -1;//0为停止，-1为未设置，使用模式值
	int release_memory_cycle_time = -1;//同上
	int max_release_memory_size = -1;//同上
}*Point_InitBaseSetShareData;

//extern int is_live_mainprocess_cycle_time;
//extern int release_memory_cycle_time;
//extern int max_release_memory_size;

extern CefRefPtr<FBroApp> fbroapp_;

//extern bool enableprocessmessage;弃用，不再判断
extern DWORD mainprocessid;//主进程ID
extern DWORD currentprocessid;//当前进程ID
extern HANDLE currenthandle;
extern std::wstring cache_path;

extern JSFunNameHandle jsfunnamehandle;
//extern ListQueryFunction Querylist;

class FBroSchemeHandlerFactory :public CefSchemeHandlerFactory
{
public:
	FBroSchemeHandlerFactory(int flag);
	FBroSchemeHandlerFactory(CefRefPtr<FBroHsResourceHandler> callback);
	CefRefPtr<FBroResourceHandler> GetFBroResourceHandler();
	~FBroSchemeHandlerFactory();

	virtual CefRefPtr<CefResourceHandler> Create(
		CefRefPtr<CefBrowser> browser,
		CefRefPtr<CefFrame> frame,
		const CefString& scheme_name,
		CefRefPtr<CefRequest> request) override;

protected:
	int m_flag = 0;
	CefRefPtr<FBroResourceHandler> m_ResourceHandler = nullptr;
private:
	IMPLEMENT_REFCOUNTING(FBroSchemeHandlerFactory);
};

void ClearMemory();


DLLEXPORT ProcessType TEXPORTS FBroGetProcessType();
DLLEXPORT BOOL TEXPORTS FBroHsInitPro(FBroInitSettings*  lpBasicInfo, CefRefPtr<FBroHsInitEvent> initevent, int defaultcache);
DLLEXPORT void TEXPORTS FBroShutdown(BOOL);
DLLEXPORT void TEXPORTS FBroDoMessageLoopWork();
DLLEXPORT void TEXPORTS FBroRunMessageLoop();
DLLEXPORT void TEXPORTS FBroQuitMessageLoop();
DLLEXPORT void TEXPORTS FBroSetOSModalLoop(bool osModalLoop);


DLLEXPORT void TEXPORTS FBroHsRegisterSchemeHandlerFactory(const CefString& in_scheme_name, const CefString& in_domain_name, CefRefPtr<FBroHsResourceHandler> callback);

DLLEXPORT BOOL TEXPORTS FBroClearSchemeHandlerFactories();

//DLLEXPORT void TEXPORTS FBroHsQueryFunctionsStatic(const CefString& js_query_function, const CefString& js_cancel_function, FBroHsQueryHandler* callback);
DLLEXPORT void TEXPORTS FBroHsQueryFunctions(const CefString& js_query_function, const CefString& js_cancel_function, CefRefPtr<FBroHsQueryHandler> callback);
DLLEXPORT void TEXPORTS FBroHsDeleteQueryFunctions(const CefString& js_query_function);


DLLEXPORT void TEXPORTS  FBroSetIsLiveMainProcessCycleTime(int indata);
DLLEXPORT void TEXPORTS  FBroSetReleaseMemoryCycleTime(int indata);
DLLEXPORT void TEXPORTS  FBroSetMaxReleaseMemory(int indata);


DLLEXPORT void TEXPORTS FBroHsDumpStart(const CefString& path, HANDLE callback);


DLLEXPORT void TEXPORTS FBroSetV8DefaultsHeapSize(int initial_heap_size, int maximum_heap_size);


DLLEXPORT void TEXPORTS FBroClearWorkingAndV8Memory();

DLLEXPORT CefRefPtr<FBroString> TEXPORTS FBroHsGetSetCachePath();

DLLEXPORT BOOL TEXPORTS FBroHsSetProcessDPI(int type);

#endif

