#pragma once

class FBroHsDevToolsMessageObserver;
class FBroHsGeneralResultCallback;
class FBroVIPUserAgentData;

class FBroVIPControl : public virtual CefBaseRefCounted
{
public:

	virtual CefRefPtr<CefBrowser> GetBrowser() = 0;
	virtual void ClearAllData() = 0;

	virtual void ClearFingerCount() = 0;
	virtual CefString GetFingerCount() = 0;

	virtual bool IsNULL() = 0;

	//指纹功能
	virtual void SetVirProductSub(const CefString& indata) = 0;
	virtual void SetVirVendor(const CefString& indata) = 0;
	virtual void SetVirVendorSub(const CefString& indata) = 0;
	virtual void SetVirUserAgent(CefRefPtr<FBroVIPUserAgentData> userAgentData) = 0;
	virtual void SetVirPlatform(const CefString& indata) = 0;
	virtual void SetVirAcceptlanguages(const CefString& indata) = 0;
	virtual void SetVirLanguages(const CefString& indata) = 0;
	virtual void SetVirAppCodeName(const CefString& indata) = 0;
	virtual void SetVirAppName(const CefString& indata) = 0;
	virtual void SetVirAppVersion(const CefString& indata) = 0;
	virtual void SetVirProduct(const CefString& indata) = 0;
	virtual void SetVirHardwareConcurrency(int indata) = 0;
	virtual void SetVirCookieEnabled(BOOL indata) = 0;
	virtual void SetVirDeviceMemory(int indata) = 0;
	virtual void SetVirJavaEnabled(BOOL indata) = 0;
	virtual void SetVirWebdriver(BOOL indata) = 0;
	virtual void SetVirOnLine(BOOL indata) = 0;
	virtual CefString SetCanvasFingerPrint_random(int minipoint, int maxpoint, int srand) = 0;
	virtual CefString SetWebGLFingerPrint_random(int minipoint, int maxpoint, int srand) = 0;
	virtual CefString SetAudioFingerPrint_random(int minipoint, int maxpoint, int srand) = 0;
	virtual void SetCanvasFingerPrint_constant(const CefString& indata) = 0;
	virtual void SetWebGLFingerPrint_constant(const CefString& indata) = 0;
	virtual void SetAudioFingerPrint_constant(const CefString& indata) = 0;
	virtual void SetPlugins(int changetype, const CefString& indata) = 0;
	virtual void SetVirCanvas2DFontFingerprint(double indata) = 0;
	virtual void SetVirCSSFontFingerprint(const CefString& indata, int x, int y) = 0;
	virtual void SetVirScreenXAndY(int X, int Y) = 0;
	virtual void SetVirScreenHeightAndWidth(int H, int W) = 0;
	virtual void SetVirScreenavailHeightAndWidth(int H, int W) = 0;
	virtual void SetVirScreencolorDepth(int indata) = 0;
	virtual void SetVirScreenpixelDepth(int indata) = 0;
	virtual void SetVirDevicePixelRatio(double indata) = 0;
	virtual void SetVirWebglvendor(const CefString& indata) = 0;
	virtual void SetVirWebglrenderer(const CefString& indata) = 0;
	virtual void SetVirRectFingerprint(int x, int y, int w, int h) = 0;
	virtual void SetVirWebrtcIP(const CefString& publicip, const CefString& localip, const CefString& host, BOOL disable) = 0;
	virtual void SetVirTimeZone(int timezonehour, int timezonemin, const CefString& timezonename, const CefString& standardtimezonename) = 0;
	virtual void SetTouchEventEmulationEnabled(BOOL enabled, int maxTouchPoints) = 0;
	virtual void SetVirBatteryManagerCharging(BOOL indata) = 0;
	virtual void SetVirBatteryManagerChargingTime(double indata) = 0;
	virtual void SetVirBatteryManagerDischargingTime(double indata) = 0;
	virtual void SetVirBatteryManagerLevel(double indata) = 0;
	virtual void SetVirLongitudeAndLatitude(double longitude, double latitude, double altitude, double accuracy, double altitude_accuracy, double heading, double speed) = 0;
	virtual void SetVirViewport(int x, int y, int w, int h) = 0;
	virtual void SetVirAudioInput(const CefString& indata) = 0;
	virtual void SetVirVideoInput(const CefString& indata) = 0;
	virtual void SetVirAudioOutput(const CefString& indata) = 0;
	virtual void SetVirKernel(int kernel) = 0;
	virtual void SetSSLCipher(int min_version, int max_version, const CefString& cipher_command) = 0;
	virtual void SetVirOrientation(int orientation, int orientation_type) = 0;
	virtual void SetVirSpeechSynthesisVoices(const CefString& indata) = 0;

	//指纹UA补充功能
    virtual void SetVirUserAgentBrands(CefRefPtr<FBroDoubleString> indata) = 0;
	virtual void SetVirUserAgentFullVersionList(CefRefPtr<FBroDoubleString> indata) = 0;
	virtual void SetVirUserAgentFullVersion(const CefString& indata) = 0;
	virtual void SetVirUserAgentPlatform(const CefString& indata) = 0;
	virtual void SetVirUserAgentPlatformVersion(const CefString& indata) = 0;
	virtual void SetVirUserAgentArchitecture(const CefString& indata) = 0;
	virtual void SetVirUserAgentModel(const CefString& indata) = 0;
	virtual void SetVirUserAgentMobile(BOOL indata) = 0;
	virtual void SetVirUserAgentBitness(const CefString& indata) = 0;
	virtual void SetVirUserAgentWow64(BOOL indata) = 0;
	virtual void SetVirUserAgentFormFactors(CefRefPtr<FBroCefStringList> indata) = 0;

	//高级功能
	virtual void SetVirisTrusted(BOOL indata) = 0;
	virtual void EnableWebsocketClientHook() = 0;
	virtual void SetEmitTouchEventsForMouse(BOOL enable, int configuration) = 0;
	virtual void SetDisableDebugger(BOOL indata) = 0;
	virtual void SetS5Auth(const CefString& url, const CefString& username, const CefString& password, BOOL closeMsg) = 0;
	virtual void ClearS5Auth() = 0;
	virtual void SetDisableConsoleDebug(BOOL indata) = 0;
	virtual void AddTabAt(const CefString&, int, BOOL, CefRefPtr<CefDictionaryValue>, CefRefPtr<FBroHsBroEvent>, const Event_Disable_Control&, const CefString&) = 0;//新建tab标签


	//开发者消息相关
	virtual void SendDevToolsMessage(const CefString& message) = 0;
	virtual void ExecuteDevToolsMethod(int message_id, const CefString& method, CefRefPtr<CefDictionaryValue> params) = 0;
	virtual BOOL AddDevToolsMessageObserver(CefRefPtr<FBroHsDevToolsMessageObserver> event) = 0;
	virtual BOOL DeleteDevToolsMessageObserver() = 0;


	//开发者消息扩展功能相关
	virtual void PageCaptureScreenshot(const CefString& format, int quality, VIEWPORT_POINT viewport, BOOL fromSurface, BOOL captureBeyondViewport, CefRefPtr<FBroHsGeneralResultCallback> object, HANDLE callback, M_POINTER arg) = 0;
	virtual void RuntimeEnable(BOOL enable) = 0;
	virtual CefRefPtr<CefListValue> PageGetContextID() = 0;
	virtual void RuntimeEvaluate(const CefString& expression, BOOL includeCommandLineAPI, int contextId, BOOL silent, BOOL userGesture, int timeout, BOOL disableBreaks, BOOL replMode, CefRefPtr<FBroHsGeneralResultCallback> object, HANDLE callback, M_POINTER arg) = 0;
	virtual void RuntimeEvaluate_FrameID(const CefString& expression, BOOL includeCommandLineAPI, int type, int frameNum, const CefString& frameId, BOOL silent, BOOL userGesture, int timeout, BOOL disableBreaks, BOOL replMode, CefRefPtr<FBroHsGeneralResultCallback> object, HANDLE callback, M_POINTER arg) = 0;
	virtual void DispatchTouchEvent(int type, E_DEV_TOUCHPOINT* touchPoints, int modifiers) = 0;
	virtual void DispatchKeyEvent(const CefString& type, int modifiers, const CefString& text, const CefString& unmodifiedText, const CefString& keyIdentifier, const CefString& code, const CefString& key, int windowsVirtualKeyCode, int nativeVirtualKeyCode, BOOL autoRepeat, BOOL isKeypad, BOOL isSystemKey, int location) = 0;
	virtual void DispatchMouseEvent(const CefString& type, int x, int y, int modifiers, const CefString& button, int buttons, int clickCount, int deltaX, int deltaY, const CefString& pointerType) = 0;

	//拦截获取相关
	virtual void AddResourceHandlerChangeData(int find_type, const CefString& url, const CefString& mini_type, const std::multimap<CefString, CefString>& header_map, void* change_data, size_t data_size) = 0;
	virtual void AddResourceHandlerChangeFile(int find_type, const CefString& url, const CefString& mini_type, const std::multimap<CefString, CefString>& header_map, std::string file_path) = 0;
	virtual void DeleteResourceHandlerChangeData(const CefString& url) = 0;
	virtual void DeleteResourceHandlerAllData() = 0;
	virtual void AddResponseFilterChangeData(int find_type, const CefString& url, int change_type, const CefString& key, const CefString& change_data) = 0;
	virtual void DeletResponseFiltereChangeData(const CefString& url) = 0;
	virtual void DeleteResponseFilterAllData() = 0;

	//内核开关相关
	virtual void SetDisableConsoleWarn(BOOL indata) = 0;
	virtual void SetDisableConsoleError(BOOL indata) = 0;
	virtual void SetDisableConsoleInfo(BOOL indata) = 0;
	virtual void SetDisableConsoleLog(BOOL indata) = 0;
	virtual void SetDisableConsoleAssert(BOOL indata) = 0;
	virtual void SetDisableConsoleDir(BOOL indata) = 0;
	virtual void SetDisableConsoleTable(BOOL indata) = 0;
	virtual void SetDisableConsoleGroup(BOOL indata) = 0;
	virtual void SetDisableConsoleTime(BOOL indata) = 0;
	virtual void SetDisableConsoleProfile(BOOL indata) = 0;
	virtual void SetDisableConsoleCount(BOOL indata) = 0;
	virtual void SetDisableConsoleTrace(BOOL indata) = 0;
	virtual void SetDisableConsoleClear(BOOL indata) = 0;
	virtual void SetDisablePerformanceCheck(BOOL disable, double min, double max) = 0;
	virtual void SetCSSKernel(int kernel) = 0;
	virtual void SetWebFeatureKernel(int kernel) = 0;
	virtual void SetV8Kernel(int kernel) = 0;
};

