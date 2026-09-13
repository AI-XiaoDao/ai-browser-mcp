#pragma once
#ifndef FBROWSER_LISTVALUE_H_
#define FBROWSER_LISTVALUE_H_

class FBroString;

DLLEXPORT CefRefPtr<FBroString> TEXPORTS FBroHsListValue_GetString(CefRefPtr<CefListValue> ListValue, int index);
DLLEXPORT CefRefPtr<CefBinaryValue> TEXPORTS FBroHsListValue_GetBinary(CefRefPtr<CefListValue> ListValue, int index);
DLLEXPORT BOOL TEXPORTS FBroHsListValue_SetBinary(CefRefPtr<CefListValue> ListValue, int index, CefRefPtr<CefBinaryValue> inValue);
DLLEXPORT CefRefPtr<CefListValue> TEXPORTS FBroHsListValue_Create();
DLLEXPORT BOOL TEXPORTS FBroHsListValue_IsValid(CefRefPtr<CefListValue> ListValue);
DLLEXPORT BOOL TEXPORTS FBroHsListValue_IsOwned(CefRefPtr<CefListValue> ListValue);
DLLEXPORT BOOL TEXPORTS FBroHsListValue_IsReadOnly(CefRefPtr<CefListValue> ListValue);
DLLEXPORT BOOL TEXPORTS FBroHsListValue_IsSame(CefRefPtr<CefListValue> ListValue, CefRefPtr<CefListValue> that);
DLLEXPORT BOOL TEXPORTS FBroHsListValue_IsEqual(CefRefPtr<CefListValue> ListValue, CefRefPtr<CefListValue> that);
DLLEXPORT CefRefPtr<CefListValue> TEXPORTS FBroHsListValue_Copy(CefRefPtr<CefListValue> ListValue);
DLLEXPORT BOOL TEXPORTS FBroHsListValue_SetSize(CefRefPtr<CefListValue> ListValue, int size);
DLLEXPORT int TEXPORTS FBroHsListValue_GetSize(CefRefPtr<CefListValue> ListValue);
DLLEXPORT BOOL TEXPORTS FBroHsListValue_Clear(CefRefPtr<CefListValue> ListValue);
DLLEXPORT BOOL TEXPORTS FBroHsListValue_Remove(CefRefPtr<CefListValue> ListValue, int index);
DLLEXPORT CefValueType TEXPORTS FBroHsListValue_GetType(CefRefPtr<CefListValue> ListValue, int index);
DLLEXPORT BOOL TEXPORTS FBroHsListValue_GetBool(CefRefPtr<CefListValue> ListValue, int index);
DLLEXPORT int TEXPORTS FBroHsListValue_GetInt(CefRefPtr<CefListValue> ListValue, int index);
DLLEXPORT double TEXPORTS FBroHsListValue_GetDouble(CefRefPtr<CefListValue> ListValue, int index);
DLLEXPORT BOOL TEXPORTS FBroHsListValue_SetNull(CefRefPtr<CefListValue> ListValue, int index);
DLLEXPORT BOOL TEXPORTS FBroHsListValue_SetBool(CefRefPtr<CefListValue> ListValue, int index, BOOL value);
DLLEXPORT BOOL TEXPORTS FBroHsListValue_SetInt(CefRefPtr<CefListValue> ListValue, int index, int value);
DLLEXPORT BOOL TEXPORTS FBroHsListValue_SetDouble(CefRefPtr<CefListValue> ListValue, int index, double value);
DLLEXPORT BOOL TEXPORTS FBroHsListValue_SetString(CefRefPtr<CefListValue> ListValue, int index, const CefString& value);
DLLEXPORT CefRefPtr<CefValue> TEXPORTS FBroHsListValue_GetValue(CefRefPtr<CefListValue> ListValue, size_t index);
DLLEXPORT CefRefPtr<CefDictionaryValue> TEXPORTS FBroHsListValue_GetDictionary(CefRefPtr<CefListValue> ListValue, size_t index);
DLLEXPORT CefRefPtr<CefListValue> TEXPORTS FBroHsListValue_GetList(CefRefPtr<CefListValue> ListValue, size_t index);
DLLEXPORT BOOL TEXPORTS FBroHsListValue_SetValue(CefRefPtr<CefListValue> ListValue, size_t index, CefRefPtr<CefValue> value);
DLLEXPORT BOOL TEXPORTS FBroHsListValue_SetDictionary(CefRefPtr<CefListValue> ListValue, size_t index, CefRefPtr<CefDictionaryValue> value);
DLLEXPORT BOOL TEXPORTS FBroHsListValue_SetList(CefRefPtr<CefListValue> ListValue, size_t index, CefRefPtr<CefListValue> value);

#endif