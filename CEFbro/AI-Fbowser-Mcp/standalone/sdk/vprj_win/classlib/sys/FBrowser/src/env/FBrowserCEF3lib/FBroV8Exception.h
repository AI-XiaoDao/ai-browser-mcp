#pragma once
#ifndef FBROWSER_V8EXCEPTION_H_
#define FBROWSER_V8EXCEPTION_H_

class FBroString;


#ifndef _FBROELIB

DLLEXPORT CefRefPtr<FBroString> TEXPORTS FBroHsV8Exception_GetMessage(CefRefPtr<CefV8Exception> object);
DLLEXPORT CefRefPtr<FBroString> TEXPORTS FBroHsV8Exception_GetSourceLine(CefRefPtr<CefV8Exception> object);
DLLEXPORT CefRefPtr<FBroString> TEXPORTS FBroHsV8Exception_GetScriptResourceName(CefRefPtr<CefV8Exception> object);
DLLEXPORT int TEXPORTS FBroHsV8Exception_GetLineNumber(CefRefPtr<CefV8Exception> object);
DLLEXPORT int TEXPORTS FBroHsV8Exception_GetStartPosition(CefRefPtr<CefV8Exception> object);
DLLEXPORT int TEXPORTS FBroHsV8Exception_GetEndPosition(CefRefPtr<CefV8Exception> object);
DLLEXPORT int TEXPORTS FBroHsV8Exception_GetStartColumn(CefRefPtr<CefV8Exception> object);
DLLEXPORT int TEXPORTS FBroHsV8Exception_GetEndColumn(CefRefPtr<CefV8Exception> object);

#endif // !_FBROELIB



////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

#endif