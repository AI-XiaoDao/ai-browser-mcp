#pragma once
#ifndef FBROWSER_V8STACK_H_
#define FBROWSER_V8STACK_H_

class FBroString;

#ifndef _FBROELIB

DLLEXPORT CefRefPtr<CefV8StackTrace> TEXPORTS FBroHsStackTrace_GetCurrent(int frame_limit);
DLLEXPORT BOOL TEXPORTS FBroHsStackTrace_IsValid(CefRefPtr<CefV8StackTrace> Object);
DLLEXPORT int TEXPORTS FBroHsStackTrace_GetFrameCount(CefRefPtr<CefV8StackTrace> Object);
DLLEXPORT CefRefPtr<CefV8StackFrame> TEXPORTS FBroHsStackTrace_GetFrame(CefRefPtr<CefV8StackTrace> Object, int index);

DLLEXPORT BOOL TEXPORTS FBroHsV8StackFrame_IsValid(CefRefPtr<CefV8StackFrame> Object);
DLLEXPORT CefRefPtr<FBroString> TEXPORTS FBroHsV8StackFrame_GetScriptName(CefRefPtr<CefV8StackFrame> Object);
DLLEXPORT CefRefPtr<FBroString> TEXPORTS FBroHsV8StackFrame_GetScriptNameOrSourceURL(CefRefPtr<CefV8StackFrame> Object);
DLLEXPORT CefRefPtr<FBroString> TEXPORTS FBroHsV8StackFrame_GetFunctionName(CefRefPtr<CefV8StackFrame> Object);
DLLEXPORT int TEXPORTS FBroHsV8StackFrame_GetLineNumber(CefRefPtr<CefV8StackFrame> Object);
DLLEXPORT int TEXPORTS FBroHsV8StackFrame_GetColumn(CefRefPtr<CefV8StackFrame> Object);
DLLEXPORT BOOL TEXPORTS FBroHsV8StackFrame_IsEval(CefRefPtr<CefV8StackFrame> Object);
DLLEXPORT BOOL TEXPORTS FBroHsV8StackFrame_IsConstructor(CefRefPtr<CefV8StackFrame> Object);

#endif // !_FBROELIB




#endif