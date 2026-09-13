#pragma once
#ifndef FBROWSER_DICTIONARYVALUE_H_
#define FBROWSER_DICTIONARYVALUE_H_

class FBroString;
class FBroCefStringList;

DLLEXPORT CefRefPtr<FBroString> TEXPORTS FBroHsDictionaryValue_GetString(CefRefPtr<CefDictionaryValue> Value, const CefString& key);
DLLEXPORT CefRefPtr<CefBinaryValue> TEXPORTS FBroHsDictionaryValue_GetBinary(CefRefPtr<CefDictionaryValue> Value, const CefString& key);
DLLEXPORT BOOL TEXPORTS FBroHsDictionaryValue_SetBinary(CefRefPtr<CefDictionaryValue> Value, const CefString& key, CefRefPtr<CefBinaryValue> inValue);
DLLEXPORT CefRefPtr<CefDictionaryValue> TEXPORTS FBroHsDictionaryValue_GetDictionary(CefRefPtr<CefDictionaryValue> Value, const CefString& key);
DLLEXPORT CefRefPtr<CefListValue> TEXPORTS FBroHsDictionaryValue_GetList(CefRefPtr<CefDictionaryValue> Value, const CefString& key);
DLLEXPORT CefRefPtr<CefDictionaryValue> TEXPORTS FBroHsDictionaryValue_Create();
DLLEXPORT BOOL TEXPORTS FBroHsDictionaryValue_IsValid(CefRefPtr<CefDictionaryValue> Value);
DLLEXPORT BOOL TEXPORTS FBroHsDictionaryValue_IsOwned(CefRefPtr<CefDictionaryValue> Value);
DLLEXPORT BOOL TEXPORTS FBroHsDictionaryValue_IsReadOnly(CefRefPtr<CefDictionaryValue> Value);
DLLEXPORT BOOL TEXPORTS FBroHsDictionaryValue_IsSame(CefRefPtr<CefDictionaryValue> Value, CefRefPtr<CefDictionaryValue> that);
DLLEXPORT BOOL TEXPORTS FBroHsDictionaryValue_IsEqual(CefRefPtr<CefDictionaryValue> Value, CefRefPtr<CefDictionaryValue> that);
DLLEXPORT CefRefPtr<CefDictionaryValue> TEXPORTS FBroHsDictionaryValue_Copy(CefRefPtr<CefDictionaryValue> Value, BOOL exclude_empty_children);
DLLEXPORT int TEXPORTS FBroHsDictionaryValue_GetSize(CefRefPtr<CefDictionaryValue> Value);
DLLEXPORT BOOL TEXPORTS FBroHsDictionaryValue_Clear(CefRefPtr<CefDictionaryValue> Value);
DLLEXPORT BOOL TEXPORTS FBroHsDictionaryValue_HasKey(CefRefPtr<CefDictionaryValue> Value, const CefString& key);
DLLEXPORT CefRefPtr<FBroCefStringList> TEXPORTS FBroHsDictionaryValue_GetKeys(CefRefPtr<CefDictionaryValue> Value);//使用后需要释放,count为分配后的wchar_t个数
DLLEXPORT BOOL TEXPORTS FBroHsDictionaryValue_Remove(CefRefPtr<CefDictionaryValue> Value, const CefString& key);
DLLEXPORT int TEXPORTS FBroHsDictionaryValue_GetType(CefRefPtr<CefDictionaryValue> Value, const CefString& key);
DLLEXPORT CefRefPtr<CefValue> TEXPORTS FBroHsDictionaryValue_GetValue(CefRefPtr<CefDictionaryValue> Value, const CefString& key);
DLLEXPORT BOOL TEXPORTS FBroHsDictionaryValue_GetBool(CefRefPtr<CefDictionaryValue> Value, const CefString& key);
DLLEXPORT int TEXPORTS FBroHsDictionaryValue_GetInt(CefRefPtr<CefDictionaryValue> Value, const CefString& key);
DLLEXPORT double TEXPORTS FBroHsDictionaryValue_GetDouble(CefRefPtr<CefDictionaryValue> Value, const CefString& key);
DLLEXPORT BOOL TEXPORTS FBroHsDictionaryValue_SetValue(CefRefPtr<CefDictionaryValue> Value, CefRefPtr<CefValue> value, const CefString& key);
DLLEXPORT BOOL TEXPORTS FBroHsDictionaryValue_SetNull(CefRefPtr<CefDictionaryValue> Value, const CefString& key);
DLLEXPORT BOOL TEXPORTS FBroHsDictionaryValue_SetBool(CefRefPtr<CefDictionaryValue> Value, const CefString& key, BOOL value);
DLLEXPORT BOOL TEXPORTS FBroHsDictionaryValue_SetInt(CefRefPtr<CefDictionaryValue> Value, const CefString& key, int value);
DLLEXPORT BOOL TEXPORTS FBroHsDictionaryValue_SetDouble(CefRefPtr<CefDictionaryValue> Value, const CefString& key, double value);
DLLEXPORT BOOL TEXPORTS FBroHsDictionaryValue_SetString(CefRefPtr<CefDictionaryValue> Value, const CefString& key, const CefString& value);
DLLEXPORT BOOL TEXPORTS FBroHsDictionaryValue_SetDictionary(CefRefPtr<CefDictionaryValue> Value, CefRefPtr<CefDictionaryValue> inObject, const CefString& key);
DLLEXPORT BOOL TEXPORTS FBroHsDictionaryValue_SetList(CefRefPtr<CefDictionaryValue> Value, CefRefPtr<CefListValue> inObject, const CefString& key);

#endif