#ifndef FBROVIPINTERFACE_H
#define FBROVIPINTERFACE_H

#pragma once

//#ifndef M_POINTER
//#ifdef _WIN64
//typedef long long M_POINTER;
//#else
//typedef long M_POINTER;
//#endif // _WIN64
//#endif
//
//#ifndef VIEWPORT
//typedef struct VIEWPORT
//{
//	int x;
//	int y;
//	int width;
//	int height;
//	int scale;
//}*VIEWPORT_POINT;
//#endif
//
//#ifndef E_DEV_TOUCHPOINT
//typedef struct E_DEV_TOUCHPOINT {
//	int x;//横坐标
//	int y;//纵坐标
//	int radiusX;//横半径
//	int radiusY;//纵半径
//	int rotationAngle;//旋转角度
//	int force;//压力
//	int id;
//}*POINT_DEV_TOUCHPOINT;
//#endif

class FBroString;
class FBroHsDevToolsMessageObserver;
class FBroHsGeneralResultCallback;
class CefBrowser;

#ifndef _FBROELIB
DLLEXPORT CefRefPtr<FBroString> TEXPORTS FBroHsBrowser_GetMachineCode();
DLLEXPORT void TEXPORTS FBroHsBrowser_SetLicenceKey(const CefString& keydata);
DLLEXPORT BOOL TEXPORTS FBroBrowser_IsLicenceKey();

DLLEXPORT BOOL TEXPORTS FBroHsOnlineLicenseControl_SetKey(const CefString& key);
DLLEXPORT CefRefPtr<FBroString> TEXPORTS FBroHsOnlineLicenseControl_GetShowLicenseType();
DLLEXPORT CefRefPtr<FBroString> TEXPORTS FBroHsOnlineLicenseControl_GetShowLicenseStartDate();
DLLEXPORT CefRefPtr<FBroString> TEXPORTS FBroHsOnlineLicenseControl_GetShowLicenseEndDate();
DLLEXPORT CefRefPtr<FBroString> TEXPORTS FBroHsOnlineLicenseControl_GetShowLicenseDevTool();
DLLEXPORT CefRefPtr<FBroString> TEXPORTS FBroHsOnlineLicenseControl_GetShowLicenseFunction();
DLLEXPORT CefRefPtr<FBroString> TEXPORTS FBroHsOnlineLicenseControl_GetShowLicenseSysVersion();
DLLEXPORT CefRefPtr<FBroString> TEXPORTS FBroHsOnlineLicenseControl_GetError();



DLLEXPORT CefRefPtr<FBroString> TEXPORTS FBroHsBrowser_GetExpirationTime();
DLLEXPORT CefRefPtr<FBroString> TEXPORTS FBroHsBrowser_GetRegistrationTime();
DLLEXPORT CefRefPtr<FBroString> TEXPORTS FBroHsBrowser_GetVersionStr();
DLLEXPORT CefRefPtr<FBroString> TEXPORTS FBroHsBrowser_GetFunctionStr();


DLLEXPORT void TEXPORTS FBroHsDevToolsDOM_enable(CefRefPtr<CefBrowser> browser, const CefString& includeWhitespace);
DLLEXPORT void TEXPORTS FBroHsDevToolsDOM_disable(CefRefPtr<CefBrowser> browser);
DLLEXPORT void TEXPORTS FBroHsDevToolsDOM_focusElement(CefRefPtr<CefBrowser> browser, int nodeId);
DLLEXPORT void TEXPORTS FBroHsDevToolsDOM_removeAttribute(CefRefPtr<CefBrowser> browser, int nodeId, const CefString& name);
DLLEXPORT void TEXPORTS FBroHsDevToolsDOM_removeNode(CefRefPtr<CefBrowser> browser, int nodeId);
DLLEXPORT void TEXPORTS FBroHsDevToolsDOM_setAttributesAsText(CefRefPtr<CefBrowser> browser, int nodeId, const CefString& text, const CefString& name);
DLLEXPORT void TEXPORTS FBroHsDevToolsDOM_setAttributeValue(CefRefPtr<CefBrowser> browser, int nodeId, const CefString& name, const CefString& value);
DLLEXPORT void TEXPORTS FBroHsDevToolsDOM_setNodeValue(CefRefPtr<CefBrowser> browser, int nodeId, const CefString& value);
DLLEXPORT void TEXPORTS FBroHsDevToolsDOM_setOuterHTML(CefRefPtr<CefBrowser> browser, int nodeId, const CefString& outerHTML);
DLLEXPORT void TEXPORTS FBroHsDevToolsDOM_discardSearchResults(CefRefPtr<CefBrowser> browser, const CefString& searchId);
DLLEXPORT void TEXPORTS FBroHsDevToolsDOM_getDocument(CefRefPtr<CefBrowser> browser, int depth, BOOL pierce, CefRefPtr<FBroHsGeneralResultCallback> object, HANDLE callback, M_POINTER arg);
DLLEXPORT void TEXPORTS FBroHsDevToolsDOM_getAttributes(CefRefPtr<CefBrowser> browser, int nodeId, CefRefPtr<FBroHsGeneralResultCallback> object, HANDLE callback, M_POINTER arg);
DLLEXPORT void TEXPORTS FBroHsDevToolsDOM_getOuterHTML(CefRefPtr<CefBrowser> browser, int nodeId, CefRefPtr<FBroHsGeneralResultCallback> object, HANDLE callback, M_POINTER arg);
DLLEXPORT void TEXPORTS FBroHsDevToolsDOM_querySelector(CefRefPtr<CefBrowser> browser, int nodeId, const CefString& selector, CefRefPtr<FBroHsGeneralResultCallback> object, HANDLE callback, M_POINTER arg);
DLLEXPORT void TEXPORTS FBroHsDevToolsDOM_querySelectorAll(CefRefPtr<CefBrowser> browser, int nodeId, const CefString& selector, CefRefPtr<FBroHsGeneralResultCallback> object, HANDLE callback, M_POINTER arg);
DLLEXPORT void TEXPORTS FBroHsDevToolsDOM_setNodeName(CefRefPtr<CefBrowser> browser, int nodeId, const CefString& name, CefRefPtr<FBroHsGeneralResultCallback> object, HANDLE callback, M_POINTER arg);
DLLEXPORT void TEXPORTS FBroHsDevToolsDOM_getContainerForNode(CefRefPtr<CefBrowser> browser, int nodeId, const CefString& containerName, CefRefPtr<FBroHsGeneralResultCallback> object, HANDLE callback, M_POINTER arg);
DLLEXPORT void TEXPORTS FBroHsDevToolsDOM_performSearch(CefRefPtr<CefBrowser> browser, const CefString& query, BOOL includeUserAgentShadowDOM, CefRefPtr<FBroHsGeneralResultCallback> object, HANDLE callback, M_POINTER arg);
DLLEXPORT void TEXPORTS FBroHsDevToolsDOM_getSearchResults(CefRefPtr<CefBrowser> browser, const CefString& searchId, int fromIndex, int toIndex, CefRefPtr<FBroHsGeneralResultCallback> object, HANDLE callback, M_POINTER arg);



//启用插件高级功能
DLLEXPORT void TEXPORTS FBroHsVIPRequestContext_EnableExtensionPlus();

//设置全局S5代理账号密码
DLLEXPORT void TEXPORTS FBroHsVIPGlobal_SetS5Auth(const CefString& username, const CefString& password, BOOL closeMsg);

//资源处理器相关
class FBroDoubleString;
DLLEXPORT void TEXPORTS FBroHsVIPResourceHandler_AddChangeData(int find_type, const CefString& url, const CefString& mini_type, CefRefPtr<FBroDoubleString> header_map, void* change_data, size_t data_size);
DLLEXPORT void TEXPORTS FBroHsVIPResourceHandler_AddChangeFile(int find_type, const CefString& url, const CefString& mini_type, CefRefPtr<FBroDoubleString> header_map, const CefString& file_path);
DLLEXPORT void TEXPORTS FBroHsVIPResourceHandler_DeleteChangeData(const CefString& url);
DLLEXPORT void TEXPORTS FBroHsVIPResourceHandler_DeleteAllData();

//资源拦截器相关
DLLEXPORT void TEXPORTS FBroHsVIPResponseFilter_AddChangeData(int find_type, const CefString& url, int change_type, const CefString& key, const CefString& change_data);
//删除全部修改数据
DLLEXPORT void TEXPORTS FBroHsVIPResponseFilter_DeleteAllData();
//删除全局url对应的修改数据
DLLEXPORT void TEXPORTS FBroHsVIPResponseFilter_DeleteChangeData(const CefString& url);

class FBroVIPControl;

//新control模式
DLLEXPORT CefRefPtr<FBroVIPControl> TEXPORTS FBroHsBrowser_GetVIPControl(CefRefPtr<CefBrowser> browser);
DLLEXPORT BOOL TEXPORTS FBroHsVIPControl_IsNULL(CefRefPtr<FBroVIPControl> vipcontrol);
DLLEXPORT CefRefPtr<CefBrowser> TEXPORTS FBroHsVIPControl_GetBrowser(CefRefPtr<FBroVIPControl> vipcontrol);
DLLEXPORT void TEXPORTS FBroHsVIPControl_ClearAllData(CefRefPtr<FBroVIPControl> vipcontrol);

//指纹功能
DLLEXPORT void TEXPORTS FBroHsVIPControl_ClearFingerCount(CefRefPtr<FBroVIPControl> vipcontrol);
DLLEXPORT CefRefPtr<FBroString> TEXPORTS FBroHsVIPControl_GetFingerCount(CefRefPtr<FBroVIPControl> vipcontrol);
DLLEXPORT void TEXPORTS FBroHsVIPControl_SetVirProductSub(CefRefPtr<FBroVIPControl> vipcontrol, const CefString& indata);
DLLEXPORT void TEXPORTS FBroHsVIPControl_SetVirVendor(CefRefPtr<FBroVIPControl> vipcontrol, const CefString& indata);
DLLEXPORT void TEXPORTS FBroHsVIPControl_SetVirVendorSub(CefRefPtr<FBroVIPControl> vipcontrol, const CefString& indata);
DLLEXPORT void TEXPORTS FBroHsVIPControl_SetVirUserAgent(CefRefPtr<FBroVIPControl> vipcontrol, CefRefPtr<FBroVIPUserAgentData> userAgentData);
DLLEXPORT void TEXPORTS FBroHsVIPControl_SetVirPlatform(CefRefPtr<FBroVIPControl> vipcontrol, const CefString& indata);
DLLEXPORT void TEXPORTS FBroHsVIPControl_SetVirAcceptlanguages(CefRefPtr<FBroVIPControl> vipcontrol, const CefString& indata);
DLLEXPORT void TEXPORTS FBroHsVIPControl_SetVirLanguages(CefRefPtr<FBroVIPControl> vipcontrol, const CefString& indata);
DLLEXPORT void TEXPORTS FBroHsVIPControl_SetVirAppCodeName(CefRefPtr<FBroVIPControl> vipcontrol, const CefString& indata);
DLLEXPORT void TEXPORTS FBroHsVIPControl_SetVirAppName(CefRefPtr<FBroVIPControl> vipcontrol, const CefString& indata);
DLLEXPORT void TEXPORTS FBroHsVIPControl_SetVirAppVersion(CefRefPtr<FBroVIPControl> vipcontrol, const CefString& indata);
DLLEXPORT void TEXPORTS FBroHsVIPControl_SetVirProduct(CefRefPtr<FBroVIPControl> vipcontrol, const CefString& indata);
DLLEXPORT void TEXPORTS FBroHsVIPControl_SetVirHardwareConcurrency(CefRefPtr<FBroVIPControl> vipcontrol, int indata);
DLLEXPORT void TEXPORTS FBroHsVIPControl_SetVirCookieEnabled(CefRefPtr<FBroVIPControl> vipcontrol, BOOL indata);
DLLEXPORT void TEXPORTS FBroHsVIPControl_SetVirDeviceMemory(CefRefPtr<FBroVIPControl> vipcontrol, int indata);
DLLEXPORT void TEXPORTS FBroHsVIPControl_SetVirJavaEnabled(CefRefPtr<FBroVIPControl> vipcontrol, BOOL indata);
DLLEXPORT void TEXPORTS FBroHsVIPControl_SetVirWebdriver(CefRefPtr<FBroVIPControl> vipcontrol, BOOL indata);
DLLEXPORT void TEXPORTS FBroHsVIPControl_SetVirOnLine(CefRefPtr<FBroVIPControl> vipcontrol, BOOL indata);
DLLEXPORT CefRefPtr<FBroString> TEXPORTS FBroHsVIPControl_SetCanvasFingerPrint_random(CefRefPtr<FBroVIPControl> vipcontrol, int minipoint, int maxpoint, int srand);
DLLEXPORT CefRefPtr<FBroString> TEXPORTS FBroHsVIPControl_SetWebGLFingerPrint_random(CefRefPtr<FBroVIPControl> vipcontrol, int minipoint, int maxpoint, int srand);
DLLEXPORT CefRefPtr<FBroString> TEXPORTS FBroHsVIPControl_SetAudioFingerPrint_random(CefRefPtr<FBroVIPControl> vipcontrol, int minipoint, int maxpoint, int srand);
DLLEXPORT void TEXPORTS FBroHsVIPControl_SetCanvasFingerPrint_constant(CefRefPtr<FBroVIPControl> vipcontrol, const CefString& indata);
DLLEXPORT void TEXPORTS FBroHsVIPControl_SetWebGLFingerPrint_constant(CefRefPtr<FBroVIPControl> vipcontrol, const CefString& indata);
DLLEXPORT void TEXPORTS FBroHsVIPControl_SetAudioFingerPrint_constant(CefRefPtr<FBroVIPControl> vipcontrol, const CefString& indata);
DLLEXPORT void TEXPORTS FBroHsVIPControl_SetPlugins(CefRefPtr<FBroVIPControl> vipcontrol, int changetype, const CefString& indata);
DLLEXPORT void TEXPORTS FBroHsVIPControl_SetVirCanvas2DFontFingerprint(CefRefPtr<FBroVIPControl> vipcontrol, double indata);
DLLEXPORT void TEXPORTS FBroHsVIPControl_SetVirCSSFontFingerprint(CefRefPtr<FBroVIPControl> vipcontrol, const CefString& indata, int x, int y);
DLLEXPORT void TEXPORTS FBroHsVIPControl_SetVirScreenXAndY(CefRefPtr<FBroVIPControl> vipcontrol, int X, int Y);
DLLEXPORT void TEXPORTS FBroHsVIPControl_SetVirScreenHeightAndWidth(CefRefPtr<FBroVIPControl> vipcontrol, int H, int W);
DLLEXPORT void TEXPORTS FBroHsVIPControl_SetVirScreenavailHeightAndWidth(CefRefPtr<FBroVIPControl> vipcontrol, int H, int W);
DLLEXPORT void TEXPORTS FBroHsVIPControl_SetVirScreencolorDepth(CefRefPtr<FBroVIPControl> vipcontrol, int indata);
DLLEXPORT void TEXPORTS FBroHsVIPControl_SetVirScreenpixelDepth(CefRefPtr<FBroVIPControl> vipcontrol, int indata);
DLLEXPORT void TEXPORTS FBroHsVIPControl_SetVirDevicePixelRatio(CefRefPtr<FBroVIPControl> vipcontrol, double indata);
DLLEXPORT void TEXPORTS FBroHsVIPControl_SetVirWebglvendor(CefRefPtr<FBroVIPControl> vipcontrol, const CefString& indata);
DLLEXPORT void TEXPORTS FBroHsVIPControl_SetVirWebglrenderer(CefRefPtr<FBroVIPControl> vipcontrol, const CefString& indata);
DLLEXPORT void TEXPORTS FBroHsVIPControl_SetVirRectFingerprint(CefRefPtr<FBroVIPControl> vipcontrol, int x, int y, int w, int h);
DLLEXPORT void TEXPORTS FBroHsVIPControl_SetVirWebrtcIP(CefRefPtr<FBroVIPControl> vipcontrol, const CefString& publicip, const CefString& localip, const CefString& host,BOOL disable);
DLLEXPORT void TEXPORTS FBroHsVIPControl_SetVirTimeZone(CefRefPtr<FBroVIPControl> vipcontrol, int timezonehour, int timezonemin, const CefString& timezonename, const CefString& standardtimezonename);
DLLEXPORT void TEXPORTS FBroHsVIPControl_SetTouchEventEmulationEnabled(CefRefPtr<FBroVIPControl> vipcontrol, BOOL enabled, int maxTouchPoints);
DLLEXPORT void TEXPORTS FBroHsVIPControl_SetVirBatteryManagerCharging(CefRefPtr<FBroVIPControl> vipcontrol, BOOL indata);
DLLEXPORT void TEXPORTS FBroHsVIPControl_SetVirBatteryManagerChargingTime(CefRefPtr<FBroVIPControl> vipcontrol, double indata);
DLLEXPORT void TEXPORTS FBroHsVIPControl_SetVirBatteryManagerDischargingTime(CefRefPtr<FBroVIPControl> vipcontrol, double indata);
DLLEXPORT void TEXPORTS FBroHsVIPControl_SetVirBatteryManagerLevel(CefRefPtr<FBroVIPControl> vipcontrol, double indata);
DLLEXPORT void TEXPORTS FBroHsVIPControl_SetVirLongitudeAndLatitude(CefRefPtr<FBroVIPControl> vipcontrol, double longitude, double latitude, double altitude, double accuracy, double altitude_accuracy, double heading, double speed);
DLLEXPORT void TEXPORTS FBroHsVIPControl_SetVirViewport(CefRefPtr<FBroVIPControl> vipcontrol, int x, int y, int w, int h);
DLLEXPORT void TEXPORTS FBroHsVIPControl_SetVirAudioInput(CefRefPtr<FBroVIPControl> vipcontrol, const CefString& indata);
DLLEXPORT void TEXPORTS FBroHsVIPControl_SetVirVideoInput(CefRefPtr<FBroVIPControl> vipcontrol, const CefString& indata);
DLLEXPORT void TEXPORTS FBroHsVIPControl_SetVirAudioOutput(CefRefPtr<FBroVIPControl> vipcontrol, const CefString& indata);
DLLEXPORT void TEXPORTS FBroHsVIPControl_SetVirKernel(CefRefPtr<FBroVIPControl> vipcontrol, int kernel);
DLLEXPORT void TEXPORTS FBroHsVIPControl_SetSSLCipher(CefRefPtr<FBroVIPControl> vipcontrol, int min_version, int max_version, const CefString& cipher_command);
DLLEXPORT void TEXPORTS FBroHsVIPControl_SetVirOrientation(CefRefPtr<FBroVIPControl> vipcontrol, int orientation, int orientation_type);
DLLEXPORT void TEXPORTS FBroHsVIPControl_SetVirSpeechSynthesisVoices(CefRefPtr<FBroVIPControl> vipcontrol, const CefString& indata);

DLLEXPORT CefRefPtr<FBroVIPUserAgentData> TEXPORTS FBroHsVIPUserAgentData_Create();

DLLEXPORT void TEXPORTS FBroHsVIPUserAgentData_SetMainUserAgent(CefRefPtr<FBroVIPUserAgentData> userAgentData, const CefString& indata);
DLLEXPORT void TEXPORTS FBroHsVIPUserAgentData_SetMainAcceptLanguage(CefRefPtr<FBroVIPUserAgentData> userAgentData, const CefString& indata);
DLLEXPORT void TEXPORTS FBroHsVIPUserAgentData_SetMainPlatform(CefRefPtr<FBroVIPUserAgentData> userAgentData, const CefString& indata);
DLLEXPORT CefRefPtr<FBroString> TEXPORTS FBroHsVIPUserAgentData_GetMainUserAgent(CefRefPtr<FBroVIPUserAgentData> userAgentData) ;
DLLEXPORT CefRefPtr<FBroString> TEXPORTS FBroHsVIPUserAgentData_GetMainAcceptLanguage(CefRefPtr<FBroVIPUserAgentData> userAgentData);
DLLEXPORT CefRefPtr<FBroString> TEXPORTS FBroHsVIPUserAgentData_GetMainPlatform(CefRefPtr<FBroVIPUserAgentData> userAgentData);

DLLEXPORT void TEXPORTS FBroHsVIPUserAgentData_SetBrands(CefRefPtr<FBroVIPUserAgentData> userAgentData, CefRefPtr<FBroDoubleString> indata);
DLLEXPORT void TEXPORTS FBroHsVIPUserAgentData_SetFullVersionList(CefRefPtr<FBroVIPUserAgentData> userAgentData, CefRefPtr<FBroDoubleString> indata);
DLLEXPORT void TEXPORTS FBroHsVIPUserAgentData_SetFullVersion(CefRefPtr<FBroVIPUserAgentData> userAgentData, const CefString& indata) ;
DLLEXPORT void TEXPORTS FBroHsVIPUserAgentData_SetPlatform(CefRefPtr<FBroVIPUserAgentData> userAgentData, const CefString& indata);
DLLEXPORT void TEXPORTS FBroHsVIPUserAgentData_SetPlatformVersion(CefRefPtr<FBroVIPUserAgentData> userAgentData, const CefString& indata);
DLLEXPORT void TEXPORTS FBroHsVIPUserAgentData_SetArchitecture(CefRefPtr<FBroVIPUserAgentData> userAgentData, const CefString& indata);
DLLEXPORT void TEXPORTS FBroHsVIPUserAgentData_SetModel(CefRefPtr<FBroVIPUserAgentData> userAgentData, const CefString& indata);
DLLEXPORT void TEXPORTS FBroHsVIPUserAgentData_SetMobile(CefRefPtr<FBroVIPUserAgentData> userAgentData, BOOL indata);
DLLEXPORT void TEXPORTS FBroHsVIPUserAgentData_SetBitness(CefRefPtr<FBroVIPUserAgentData> userAgentData, const CefString& indata);
DLLEXPORT void TEXPORTS FBroHsVIPUserAgentData_SetWow64(CefRefPtr<FBroVIPUserAgentData> userAgentData, BOOL indata);
DLLEXPORT void TEXPORTS FBroHsVIPUserAgentData_SetFormFactors(CefRefPtr<FBroVIPUserAgentData> userAgentData, CefRefPtr<FBroCefStringList> indata);
DLLEXPORT CefRefPtr<FBroDoubleString> TEXPORTS FBroHsVIPUserAgentData_GetBrands(CefRefPtr<FBroVIPUserAgentData> userAgentData);
DLLEXPORT CefRefPtr<FBroDoubleString> TEXPORTS FBroHsVIPUserAgentData_GetFullVersionList(CefRefPtr<FBroVIPUserAgentData> userAgentData) ;
DLLEXPORT CefRefPtr<FBroString> TEXPORTS FBroHsVIPUserAgentData_GetFullVersion(CefRefPtr<FBroVIPUserAgentData> userAgentData) ;
DLLEXPORT CefRefPtr<FBroString> TEXPORTS FBroHsVIPUserAgentData_GetPlatform(CefRefPtr<FBroVIPUserAgentData> userAgentData);
DLLEXPORT CefRefPtr<FBroString> TEXPORTS FBroHsVIPUserAgentData_GetPlatformVersion(CefRefPtr<FBroVIPUserAgentData> userAgentData) ;
DLLEXPORT CefRefPtr<FBroString> TEXPORTS FBroHsVIPUserAgentData_GetArchitecture(CefRefPtr<FBroVIPUserAgentData> userAgentData);
DLLEXPORT CefRefPtr<FBroString> TEXPORTS FBroHsVIPUserAgentData_GetModel(CefRefPtr<FBroVIPUserAgentData> userAgentData);
DLLEXPORT BOOL TEXPORTS FBroHsVIPUserAgentData_GetMobile(CefRefPtr<FBroVIPUserAgentData> userAgentData);
DLLEXPORT CefRefPtr<FBroString> TEXPORTS FBroHsVIPUserAgentData_GetBitness(CefRefPtr<FBroVIPUserAgentData> userAgentData);
DLLEXPORT BOOL TEXPORTS FBroHsVIPUserAgentData_GetWow64(CefRefPtr<FBroVIPUserAgentData> userAgentData);
DLLEXPORT CefRefPtr<FBroCefStringList> TEXPORTS FBroHsVIPUserAgentData_GetFormFactors(CefRefPtr<FBroVIPUserAgentData> userAgentData) ;

//高级功能
DLLEXPORT void TEXPORTS FBroHsVIPControl_SetVirisTrusted(CefRefPtr<FBroVIPControl> vipcontrol, BOOL indata);
DLLEXPORT void TEXPORTS FBroHsVIPControl_EnableWebsocketClientHook(CefRefPtr<FBroVIPControl> vipcontrol);
DLLEXPORT void TEXPORTS FBroHsVIPControl_SetEmitTouchEventsForMouse(CefRefPtr<FBroVIPControl> vipcontrol, BOOL enable, int configuration);
DLLEXPORT void TEXPORTS FBroHsVIPControl_SetDisableDebugger(CefRefPtr<FBroVIPControl> vipcontrol, BOOL indata);
DLLEXPORT void TEXPORTS FBroHsVIPControl_SetDisableConsoleDebug(CefRefPtr<FBroVIPControl> vipcontrol, BOOL indata);
DLLEXPORT void TEXPORTS FBroHsVIPControl_SetS5Auth(CefRefPtr<FBroVIPControl> vipcontrol, const CefString& url, const CefString& username, const CefString& password, BOOL closeMsg);
DLLEXPORT void TEXPORTS FBroHsVIPControl_ClearS5Auth(CefRefPtr<FBroVIPControl> vipcontrol);
DLLEXPORT void TEXPORTS FBroHsVIPControl_AddTabAt(CefRefPtr<FBroVIPControl> vipcontrol, const CefString& url, int index, BOOL foreground,
	CefRefPtr<CefDictionaryValue> extrainfo, CefRefPtr<FBroHsBroEvent> hsbroevent, Event_Disable_Control* eventContrl, const CefString& user_flag);

//开发者消息相关
DLLEXPORT void TEXPORTS FBroHsVIPControl_SendDevToolsMessage(CefRefPtr<FBroVIPControl> vipcontrol, const CefString& message);
DLLEXPORT void TEXPORTS FBroHsVIPControl_ExecuteDevToolsMethod(CefRefPtr<FBroVIPControl> vipcontrol, int message_id, const CefString& method, CefRefPtr<CefDictionaryValue> params);
DLLEXPORT BOOL TEXPORTS FBroHsVIPControl_AddDevToolsMessageObserver(CefRefPtr<FBroVIPControl> vipcontrol, CefRefPtr<FBroHsDevToolsMessageObserver> event);
DLLEXPORT BOOL TEXPORTS FBroHsVIPControl_DeleteDevToolsMessageObserver(CefRefPtr<FBroVIPControl> vipcontrol);

//开发者消息扩展功能相关
DLLEXPORT void TEXPORTS FBroHsVIPControl_PageCaptureScreenshot(CefRefPtr<FBroVIPControl> vipcontrol, const CefString& format, int quality, VIEWPORT_POINT viewport, BOOL fromSurface, BOOL captureBeyondViewport, CefRefPtr<FBroHsGeneralResultCallback> object, HANDLE callback, M_POINTER arg);
DLLEXPORT void TEXPORTS FBroHsVIPControl_RuntimeEnable(CefRefPtr<FBroVIPControl> vipcontrol, BOOL enable);
DLLEXPORT CefRefPtr<CefListValue> TEXPORTS FBroHsVIPControl_PageGetContextID(CefRefPtr<FBroVIPControl> vipcontrol);
DLLEXPORT void TEXPORTS FBroHsVIPControl_RuntimeEvaluate(CefRefPtr<FBroVIPControl> vipcontrol, const CefString& expression, BOOL includeCommandLineAPI, int contextId, BOOL silent, BOOL userGesture, int timeout, BOOL disableBreaks, BOOL replMode, CefRefPtr<FBroHsGeneralResultCallback> object, HANDLE callback, M_POINTER arg);
DLLEXPORT void TEXPORTS FBroHsVIPControl_RuntimeEvaluate_FrameID(CefRefPtr<FBroVIPControl> vipcontrol, const CefString& expression, BOOL includeCommandLineAPI, int type, int frameNum, const CefString& frameId, BOOL silent, BOOL userGesture, int timeout, BOOL disableBreaks, BOOL replMode, CefRefPtr<FBroHsGeneralResultCallback> object, HANDLE callback, M_POINTER arg);
DLLEXPORT void TEXPORTS FBroHsVIPControl_DispatchTouchEvent(CefRefPtr<FBroVIPControl> vipcontrol, int type, E_DEV_TOUCHPOINT* touchPoints, int modifiers);
DLLEXPORT void TEXPORTS FBroHsVIPControl_DispatchKeyEvent(CefRefPtr<FBroVIPControl> vipcontrol, const CefString& type, int modifiers, const CefString& text, const CefString& unmodifiedText, const CefString& keyIdentifier, const CefString& code, const CefString& key, int windowsVirtualKeyCode, int nativeVirtualKeyCode, BOOL autoRepeat, BOOL isKeypad, BOOL isSystemKey, int location);
DLLEXPORT void TEXPORTS FBroHsVIPControl_DispatchMouseEvent(CefRefPtr<FBroVIPControl> vipcontrol, const CefString& type, int x, int y, int modifiers, const CefString& button, int buttons, int clickCount, int deltaX, int deltaY, const CefString& pointerType);

//拦截获取相关
DLLEXPORT void TEXPORTS FBroHsVIPControl_AddResourceHandlerChangeData(CefRefPtr<FBroVIPControl> vipcontrol, int find_type, const CefString& url, const CefString& mini_type, CefRefPtr<FBroDoubleString> header_map, void* change_data, size_t data_size);
DLLEXPORT void TEXPORTS FBroHsVIPControl_AddResourceHandlerChangeFile(CefRefPtr<FBroVIPControl> vipcontrol, int find_type, const CefString& url, const CefString& mini_type, CefRefPtr<FBroDoubleString> header_map, const CefString& file_path);
DLLEXPORT void TEXPORTS FBroHsVIPControl_DeleteResourceHandlerChangeData(CefRefPtr<FBroVIPControl> vipcontrol, const CefString& url);
DLLEXPORT void TEXPORTS FBroHsVIPControl_DeleteResourceHandlerAllData(CefRefPtr<FBroVIPControl> vipcontrol);
DLLEXPORT void TEXPORTS FBroHsVIPControl_AddResponseFilterChangeData(CefRefPtr<FBroVIPControl> vipcontrol, int find_type, const CefString& url, int change_type, const CefString& key, const CefString& change_data);
DLLEXPORT void TEXPORTS FBroHsVIPControl_DeletResponseFiltereChangeData(CefRefPtr<FBroVIPControl> vipcontrol, const CefString& url);
DLLEXPORT void TEXPORTS FBroHsVIPControl_DeleteResponseFilterAllData(CefRefPtr<FBroVIPControl> vipcontrol);

//插件功能
DLLEXPORT void TEXPORTS FBroHsVIPRequestContext_LoadExtension(CefRefPtr<CefRequestContext> requestContext, const CefString& path);
DLLEXPORT void TEXPORTS FBroHsVIPRequestContext_InstallCrx(CefRefPtr<CefRequestContext> requestContext, const CefString& filePath);
DLLEXPORT void TEXPORTS FBroHsVIPRequestContext_UnstallExtension(CefRefPtr<CefRequestContext> requestContext, const CefString& extensionID);
DLLEXPORT CefRefPtr<FBroString> TEXPORTS FBroHsVIPRequestContext_GetExtensionPath(CefRefPtr<CefRequestContext> requestContext, const CefString& extensionID);
DLLEXPORT CefRefPtr<FBroString> TEXPORTS FBroHsVIPRequestContext_GetExtensionURL(CefRefPtr<CefRequestContext> requestContext, const CefString& extensionID);
DLLEXPORT CefRefPtr<FBroString> TEXPORTS FBroHsVIPRequestContext_GetExtensionName(CefRefPtr<CefRequestContext> requestContext, const CefString& extensionID);

//全局设置代理
DLLEXPORT void TEXPORTS FBroHsVIPCommandLine_SetProxy(CefRefPtr<CefCommandLine> cmd, const CefString& url, const CefString& user, const CefString& password);

//内核开关
DLLEXPORT void TEXPORTS FBroHsVIPControl_SetDisableConsoleWarn(CefRefPtr<FBroVIPControl> vipcontrol, BOOL indata);
DLLEXPORT void TEXPORTS FBroHsVIPControl_SetDisableConsoleError(CefRefPtr<FBroVIPControl> vipcontrol, BOOL indata);
DLLEXPORT void TEXPORTS FBroHsVIPControl_SetDisableConsoleInfo(CefRefPtr<FBroVIPControl> vipcontrol, BOOL indata);
DLLEXPORT void TEXPORTS FBroHsVIPControl_SetDisableConsoleLog(CefRefPtr<FBroVIPControl> vipcontrol, BOOL indata);
DLLEXPORT void TEXPORTS FBroHsVIPControl_SetDisableConsoleAssert(CefRefPtr<FBroVIPControl> vipcontrol, BOOL indata);
DLLEXPORT void TEXPORTS FBroHsVIPControl_SetDisableConsoleDir(CefRefPtr<FBroVIPControl> vipcontrol, BOOL indata);
DLLEXPORT void TEXPORTS FBroHsVIPControl_SetDisableConsoleTable(CefRefPtr<FBroVIPControl> vipcontrol, BOOL indata);
DLLEXPORT void TEXPORTS FBroHsVIPControl_SetDisableConsoleGroup(CefRefPtr<FBroVIPControl> vipcontrol, BOOL indata);
DLLEXPORT void TEXPORTS FBroHsVIPControl_SetDisableConsoleTime(CefRefPtr<FBroVIPControl> vipcontrol, BOOL indata);
DLLEXPORT void TEXPORTS FBroHsVIPControl_SetDisableConsoleProfile(CefRefPtr<FBroVIPControl> vipcontrol, BOOL indata);
DLLEXPORT void TEXPORTS FBroHsVIPControl_SetDisableConsoleCount(CefRefPtr<FBroVIPControl> vipcontrol, BOOL indata);
DLLEXPORT void TEXPORTS FBroHsVIPControl_SetDisableConsoleTrace(CefRefPtr<FBroVIPControl> vipcontrol, BOOL indata);
DLLEXPORT void TEXPORTS FBroHsVIPControl_SetDisableConsoleClear(CefRefPtr<FBroVIPControl> vipcontrol, BOOL indata);
DLLEXPORT void TEXPORTS FBroHsVIPControl_SetDisablePerformanceCheck(CefRefPtr<FBroVIPControl> vipcontrol, BOOL disable, double min, double max);
DLLEXPORT void TEXPORTS FBroHsVIPControl_SetCSSKernel(CefRefPtr<FBroVIPControl> vipcontrol, int kernel);
DLLEXPORT void TEXPORTS FBroHsVIPControl_SetWebFeatureKernel(CefRefPtr<FBroVIPControl> vipcontrol, int kernel);
DLLEXPORT void TEXPORTS FBroHsVIPControl_SetV8Kernel(CefRefPtr<FBroVIPControl> vipcontrol, int kernel);

#endif // !_FBROELIB



#endif
