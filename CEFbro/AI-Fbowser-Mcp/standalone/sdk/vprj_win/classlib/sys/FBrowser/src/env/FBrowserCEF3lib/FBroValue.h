#pragma once
#ifndef FBROWSER_VALUE_H_
#define FBROWSER_VALUE_H_

class FBroString;

DLLEXPORT CefRefPtr<CefValue> TEXPORTS FBroHsValue_Create();
DLLEXPORT BOOL TEXPORTS FBroHsValue_IsValid(CefRefPtr<CefValue> Value);
DLLEXPORT BOOL TEXPORTS FBroHsValue_IsOwned(CefRefPtr<CefValue> Value);
DLLEXPORT BOOL TEXPORTS FBroHsValue_IsReadOnly(CefRefPtr<CefValue> Value);
DLLEXPORT BOOL TEXPORTS FBroHsValue_IsSame(CefRefPtr<CefValue> Value, CefRefPtr<CefValue> that);
DLLEXPORT BOOL TEXPORTS FBroHsValue_IsEqual(CefRefPtr<CefValue> Value, CefRefPtr<CefValue> that);
DLLEXPORT CefRefPtr<CefValue> TEXPORTS FBroHsValue_Copy(CefRefPtr<CefValue> Value);
DLLEXPORT int TEXPORTS FBroHsValue_GetType(CefRefPtr<CefValue> Value);
DLLEXPORT BOOL TEXPORTS FBroHsValue_GetBool(CefRefPtr<CefValue> Value);
DLLEXPORT int TEXPORTS FBroHsValue_GetInt(CefRefPtr<CefValue> Value);
DLLEXPORT double TEXPORTS FBroHsValue_GetDouble(CefRefPtr<CefValue> Value);
DLLEXPORT BOOL TEXPORTS FBroHsValue_SetNull(CefRefPtr<CefValue> Value);
DLLEXPORT BOOL TEXPORTS FBroHsValue_SetBool(CefRefPtr<CefValue> Value, BOOL value);
DLLEXPORT BOOL TEXPORTS FBroHsValue_SetInt(CefRefPtr<CefValue> Value, int value);
DLLEXPORT BOOL TEXPORTS FBroHsValue_SetDouble(CefRefPtr<CefValue> Value, double value);
DLLEXPORT BOOL TEXPORTS FBroHsValue_SetString(CefRefPtr<CefValue> Value, const CefString& value);
DLLEXPORT BOOL TEXPORTS FBroHsValue_SetDictionary(CefRefPtr<CefValue> Value, CefRefPtr<CefDictionaryValue> tempObject);
DLLEXPORT BOOL TEXPORTS FBroHsValue_SetList(CefRefPtr<CefValue> Value, CefRefPtr<CefListValue> tempObject);
DLLEXPORT CefRefPtr<FBroString> TEXPORTS FBroHsValue_GetString(CefRefPtr<CefValue> ListValue);
DLLEXPORT CefRefPtr<CefBinaryValue> TEXPORTS FBroHsValue_GetBinary(CefRefPtr<CefValue> ListValue);
DLLEXPORT BOOL TEXPORTS FBroHsValue_SetBinary(CefRefPtr<CefValue> ListValue, CefRefPtr<CefBinaryValue> inValue);
DLLEXPORT CefRefPtr<CefDictionaryValue>  TEXPORTS FBroHsValue_GetDictionary(CefRefPtr<CefValue> Value);
DLLEXPORT CefRefPtr<CefListValue> TEXPORTS FBroHsValue_GetList(CefRefPtr<CefValue> Value);



DLLEXPORT CefRefPtr<CefBinaryValue> TEXPORTS FBroHsBinaryValue_Create(const void* data, size_t data_size);
DLLEXPORT BOOL TEXPORTS FBroHsBinaryValue_IsValid(CefRefPtr<CefBinaryValue> value);
DLLEXPORT BOOL TEXPORTS FBroHsBinaryValue_IsOwned(CefRefPtr<CefBinaryValue> value);
DLLEXPORT BOOL TEXPORTS FBroHsBinaryValue_IsSame(CefRefPtr<CefBinaryValue> value, CefRefPtr<CefBinaryValue> that);
DLLEXPORT BOOL TEXPORTS FBroHsBinaryValue_IsEqual(CefRefPtr<CefBinaryValue> value, CefRefPtr<CefBinaryValue> that);
DLLEXPORT CefRefPtr<CefBinaryValue> TEXPORTS FBroHsBinaryValue_Copy(CefRefPtr<CefBinaryValue> value);
DLLEXPORT int TEXPORTS FBroHsBinaryValue_GetSize(CefRefPtr<CefBinaryValue> value);
DLLEXPORT void TEXPORTS FBroHsBinaryValue_GetData(CefRefPtr<CefBinaryValue> value, void* buffer,size_t buffer_size,size_t data_offset);

DLLEXPORT CefRefPtr<FBroString> TEXPORTS FBroHsBinaryValue_GetString(CefRefPtr<CefBinaryValue> value);

#endif
