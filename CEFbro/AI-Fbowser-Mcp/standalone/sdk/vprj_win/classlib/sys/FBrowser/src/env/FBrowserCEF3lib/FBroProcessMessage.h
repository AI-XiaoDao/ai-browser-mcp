#pragma once
#ifndef FBROWSER_PROCESSMESSAGE_H_
#define FBROWSER_PROCESSMESSAGE_H_

class FBroString;

#ifndef _FBROELIB

DLLEXPORT CefRefPtr<CefProcessMessage> TEXPORTS FBroHsProcessMessage_Create(const CefString& name);
DLLEXPORT BOOL TEXPORTS FBroHsProcessMessage_IsValid(CefRefPtr<CefProcessMessage> ProcessMessage);
DLLEXPORT BOOL TEXPORTS FBroHsProcessMessage_IsReadOnly(CefRefPtr<CefProcessMessage> ProcessMessage);
DLLEXPORT CefRefPtr<CefProcessMessage> TEXPORTS FBroHsProcessMessage_Copy(CefRefPtr<CefProcessMessage> ProcessMessage);
DLLEXPORT CefRefPtr<FBroString> TEXPORTS FBroHsProcessMessage_GetName(CefRefPtr<CefProcessMessage> ProcessMessage);
DLLEXPORT CefRefPtr<CefListValue> TEXPORTS FBroHsProcessMessage_GetArgumentList(CefRefPtr<CefProcessMessage> ProcessMessage);

#endif // !_FBROELIB




#endif