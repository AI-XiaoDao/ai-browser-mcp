#pragma once

class FBroHsJsCallback;

#ifndef _FBROELIB

DLLEXPORT void TEXPORTS FBroHsBrowserFrameTianBiao_SetClick(CefRefPtr<CefFrame> frame, const CefString& querySelectorAll, int index);
DLLEXPORT void TEXPORTS FBroHsBrowserFrameTianBiao_SetScrollIntoView(CefRefPtr<CefFrame> frame, const CefString& querySelectorAll, int index, BOOL isTop);

DLLEXPORT void TEXPORTS FBroHsBrowserFrameTianBiao_SetChecked(CefRefPtr<CefFrame> frame, const CefString& querySelectorAll, int index, BOOL check);
//DLLEXPORT void TEXPORTS FBroHsBrowserFrameTianBiao_GetCheckedStatic(CefRefPtr<CefFrame> frame, const CefString& querySelectorAll, int index, FBroHsJsCallback* callback);
DLLEXPORT void TEXPORTS FBroHsBrowserFrameTianBiao_GetChecked(CefRefPtr<CefFrame> frame, const CefString& querySelectorAll, int index, CefRefPtr<FBroHsJsCallback> callback);

DLLEXPORT void TEXPORTS FBroHsBrowserFrameTianBiao_SetSelected(CefRefPtr<CefFrame> frame, const CefString& querySelectorAll, int index, int selectIndex);
//DLLEXPORT void TEXPORTS FBroHsBrowserFrameTianBiao_GetSelectedStatic(CefRefPtr<CefFrame> frame, const CefString& querySelectorAll, int index, FBroHsJsCallback* callback);
DLLEXPORT void TEXPORTS FBroHsBrowserFrameTianBiao_GetSelected(CefRefPtr<CefFrame> frame, const CefString& querySelectorAll, int index, CefRefPtr<FBroHsJsCallback> callback);

DLLEXPORT void TEXPORTS FBroHsBrowserFrameTianBiao_SetFocus(CefRefPtr<CefFrame> frame, const CefString& querySelectorAll, int index, BOOL focus);

DLLEXPORT void TEXPORTS FBroHsBrowserFrameTianBiao_SetValue(CefRefPtr<CefFrame> frame, const CefString& querySelectorAll, int index, const CefString& value);
//DLLEXPORT void TEXPORTS FBroHsBrowserFrameTianBiao_GetValueStatic(CefRefPtr<CefFrame> frame, const CefString& querySelectorAll, int index, FBroHsJsCallback* callback);
DLLEXPORT void TEXPORTS FBroHsBrowserFrameTianBiao_GetValue(CefRefPtr<CefFrame> frame, const CefString& querySelectorAll, int index, CefRefPtr<FBroHsJsCallback> callback);

DLLEXPORT void TEXPORTS FBroHsBrowserFrameTianBiao_SetInnerText(CefRefPtr<CefFrame> frame, const CefString& querySelectorAll, int index, const CefString& value);
//DLLEXPORT void TEXPORTS FBroHsBrowserFrameTianBiao_GetInnerTextStatic(CefRefPtr<CefFrame> frame, const CefString& querySelectorAll, int index, FBroHsJsCallback* callback);
DLLEXPORT void TEXPORTS FBroHsBrowserFrameTianBiao_GetInnerText(CefRefPtr<CefFrame> frame, const CefString& querySelectorAll, int index, CefRefPtr<FBroHsJsCallback> callback);

DLLEXPORT void TEXPORTS FBroHsBrowserFrameTianBiao_SetOuterText(CefRefPtr<CefFrame> frame, const CefString& querySelectorAll, int index, const CefString& value);
//DLLEXPORT void TEXPORTS FBroHsBrowserFrameTianBiao_GetOuterTextStatic(CefRefPtr<CefFrame> frame, const CefString& querySelectorAll, int index, FBroHsJsCallback* callback);
DLLEXPORT void TEXPORTS FBroHsBrowserFrameTianBiao_GetOuterText(CefRefPtr<CefFrame> frame, const CefString& querySelectorAll, int index, CefRefPtr<FBroHsJsCallback> callback);

DLLEXPORT void TEXPORTS FBroHsBrowserFrameTianBiao_SetInnerHTML(CefRefPtr<CefFrame> frame, const CefString& querySelectorAll, int index, const CefString& value);
//DLLEXPORT void TEXPORTS FBroHsBrowserFrameTianBiao_GetInnerHTMLStatic(CefRefPtr<CefFrame> frame, const CefString& querySelectorAll, int index, FBroHsJsCallback* callback);
DLLEXPORT void TEXPORTS FBroHsBrowserFrameTianBiao_GetInnerHTML(CefRefPtr<CefFrame> frame, const CefString& querySelectorAll, int index, CefRefPtr<FBroHsJsCallback> callback);

DLLEXPORT void TEXPORTS FBroHsBrowserFrameTianBiao_SetOuterHTML(CefRefPtr<CefFrame> frame, const CefString& querySelectorAll, int index, const CefString& value);
//DLLEXPORT void TEXPORTS FBroHsBrowserFrameTianBiao_GetOuterHTMLStatic(CefRefPtr<CefFrame> frame, const CefString& querySelectorAll, int index, FBroHsJsCallback* callback);
DLLEXPORT void TEXPORTS FBroHsBrowserFrameTianBiao_GetOuterHTML(CefRefPtr<CefFrame> frame, const CefString& querySelectorAll, int index, CefRefPtr<FBroHsJsCallback> callback);

DLLEXPORT void TEXPORTS FBroHsBrowserFrameTianBiao_SetAttribute(CefRefPtr<CefFrame> frame, const CefString& querySelectorAll, int index, const CefString& name, const CefString& value);
//DLLEXPORT void TEXPORTS FBroHsBrowserFrameTianBiao_GetAttributeStatic(CefRefPtr<CefFrame> frame, const CefString& querySelectorAll, int index, const CefString& name, FBroHsJsCallback* callback);
DLLEXPORT void TEXPORTS FBroHsBrowserFrameTianBiao_GetAttribute(CefRefPtr<CefFrame> frame, const CefString& querySelectorAll, int index, const CefString& name, CefRefPtr<FBroHsJsCallback> callback);

//DLLEXPORT void TEXPORTS FBroHsBrowserFrameTianBiao_HasAttributeStatic(CefRefPtr<CefFrame> frame, const CefString& querySelectorAll, int index, FBroHsJsCallback* callback);
DLLEXPORT void TEXPORTS FBroHsBrowserFrameTianBiao_HasAttribute(CefRefPtr<CefFrame> frame, const CefString& querySelectorAll, int index, CefRefPtr<FBroHsJsCallback> callback);

//DLLEXPORT void TEXPORTS FBroHsBrowserFrameTianBiao_GetPointStatic(CefRefPtr<CefFrame> frame, const CefString& querySelectorAll, int index, FBroHsJsCallback* callback);
DLLEXPORT void TEXPORTS FBroHsBrowserFrameTianBiao_GetPoint(CefRefPtr<CefFrame> frame, const CefString& querySelectorAll, int index, CefRefPtr<FBroHsJsCallback> callback);

DLLEXPORT void TEXPORTS FBroHsBrowserFrameTianBiao_DispatchEvent(CefRefPtr<CefFrame> frame, const CefString& querySelectorAll, int index, const CefString& eventFlag, int keyCode);

#endif // !_FBROELIB


