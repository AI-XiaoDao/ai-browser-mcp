#pragma once

class FBroHsBroEvent;
class FBroString;

//主要用于事件中弹出子窗口的事件和额外信息设置的功能
class FBroUseExtraData : public virtual CefBaseRefCounted {
public:
	virtual void SetEvent(CefRefPtr<FBroHsBroEvent> event) = 0;
	virtual CefRefPtr<FBroHsBroEvent> GetEvent() = 0;
	virtual void SetData(const Event_Disable_Control& eventDisableControl) = 0;
	virtual void SetData(CefRefPtr<CefDictionaryValue> extra_info) = 0;
	virtual void SetData(const CefString& user_flag) = 0;
	virtual Event_Disable_Control& GetEventDisableControlData() = 0;
	virtual CefRefPtr<CefDictionaryValue> GetExtraInfoData() = 0;
	virtual CefString GetUserFlagData() = 0;

protected:
	IMPLEMENT_REFCOUNTING(FBroUseExtraData);
};

//内置使用非接口
CefRefPtr<FBroUseExtraData> FBroHsUseExtraData_Creat();

DLLEXPORT void TEXPORTS FBroHsUseExtraData_SetEvent(CefRefPtr<FBroUseExtraData> extra, CefRefPtr<FBroHsBroEvent> event);
DLLEXPORT CefRefPtr<FBroHsBroEvent> TEXPORTS FBroHsUseExtraData_GetEvent(CefRefPtr<FBroUseExtraData> extra);
DLLEXPORT void TEXPORTS FBroHsUseExtraData_SetEventDisableControlData(CefRefPtr<FBroUseExtraData> extra, Event_Disable_Control* eventDisableControl);
DLLEXPORT void TEXPORTS FBroHsUseExtraData_SetExtraInfoData(CefRefPtr<FBroUseExtraData> extra, CefRefPtr<CefDictionaryValue> extra_info);
DLLEXPORT void TEXPORTS FBroHsUseExtraData_SetUserFlagData(CefRefPtr<FBroUseExtraData> extra, const CefString& user_flag);
DLLEXPORT Event_Disable_Control TEXPORTS FBroHsUseExtraData_GetEventDisableControlData(CefRefPtr<FBroUseExtraData> extra);
DLLEXPORT CefRefPtr<CefDictionaryValue> TEXPORTS FBroHsUseExtraData_GetExtraInfoData(CefRefPtr<FBroUseExtraData> extra);
DLLEXPORT CefRefPtr<FBroString> TEXPORTS FBroHsUseExtraData_GetUserFlagData(CefRefPtr<FBroUseExtraData> extra);