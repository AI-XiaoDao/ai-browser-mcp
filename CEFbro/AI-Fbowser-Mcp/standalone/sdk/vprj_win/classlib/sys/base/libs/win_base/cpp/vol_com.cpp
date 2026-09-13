
// Copyright (C) Recursion Company. All rights reserved.

#include "../vol_base.h"

// {8AB1733C-F55B-4347-A61C-B257280F9967}
const IID IID_IVolComRecordObject = { 0x8ab1733c, 0xf55b, 0x4347, { 0xa6, 0x1c, 0xb2, 0x57, 0x28, 0xf, 0x99, 0x67 } };

void STDMETHODCALLTYPE CVolComRecordObject::TakeOverVolObject (CVolObject* pVolObject)
{
    if (pVolObject != m_pVolObject)
    {
        if (m_pVolObject != NULL)
            m_pVolObject->Destroy ();

        m_pVolObject = pVolObject;
    }
}

HRESULT STDMETHODCALLTYPE CVolComRecordObject::QueryInterface (REFIID riid, void** ppvObject)
{
    if (riid == __uuidof (IUnknown))
    {
        *ppvObject = static_cast<IUnknown*> (this);
    }
    else if (riid == __uuidof (IVolComObject))
    {
        *ppvObject = static_cast<IVolComObject*> (this);
    }
    else
    {
        *ppvObject = NULL;
        return E_NOINTERFACE;
    }

    reinterpret_cast<IUnknown*>(*ppvObject)->AddRef ();
    return S_OK;
}

ULONG STDMETHODCALLTYPE CVolComRecordObject::AddRef (void)
{
    return ::InterlockedIncrement (&m_lRefCount);
}

ULONG STDMETHODCALLTYPE CVolComRecordObject::Release (void)
{
    const LONG res = ::InterlockedDecrement (&m_lRefCount);
    if (res == 0)
        delete this;
    return res;
}

CVolObject* CVolComRecordObject::sGetVolObject (IUnknown* punkVal)
{
    CVolObject* pVolObject = NULL;

    if (punkVal != NULL)
    {
        IVolComObject* pVolComObject;
        if (SUCCEEDED (punkVal->QueryInterface (__uuidof (IVolComObject), (void**)&pVolComObject)))
        {
            pVolObject = pVolComObject->GetVolObject ();
            pVolComObject->Release ();
        }
    }

    return pVolObject;
}

CVolObject& CVolComRecordObject::sGetVolObject (IUnknown* punkVal, CVolRuntimeClass* pRuntimeClass, CVolObjectDestroyer& objDestroyer)
{
    ASSERT (pRuntimeClass != NULL);

    CVolObject* pVolObject = sGetVolObject (punkVal);

    if (pVolObject == NULL || pVolObject->IsVolInstanceOf (pRuntimeClass) == FALSE)
    {
        pVolObject = pRuntimeClass->CreateObject ();
        pVolObject->SetNullObjectFlag ();
        objDestroyer.SetVolObject (pVolObject);
    }

    return *pVolObject;
}

CVolComRecordObject* CVolComRecordObject::sCreateNew (CVolObject* pVoldObjectCopyFrom)
{
    CVolComRecordObject* pVolComObject = new CVolComRecordObject;
    if (pVoldObjectCopyFrom != NULL)
        pVolComObject->TakeOverVolObject (pVoldObjectCopyFrom->MakeCloneObject ());

    return pVolComObject;
}

//------------------------------------------------------------------------------------------------

void CVolComVariant::_CopySelfFrom (const CVolComVariant& objCopyFrom)
{
    ::VariantCopy (&m_var, &objCopyFrom.m_var);
}

BOOL CVolComVariant::_IsSelfEqual (const CVolComVariant& objCompare) const
{
    return (::VarCmp ((VARIANT*)&m_var, (VARIANT*)&objCompare.m_var, LOCALE_USER_DEFAULT) == VARCMP_EQ);
}

VOL_VARIANT_TYPE CVolComVariant::GetType () const
{
    switch (m_var.vt)
    {
    case VT_EMPTY:                return VVT_EMPTY;
    case VT_I1:
    case VT_UI1:                  return VVT_SBYTE;
    case VT_I2:
    case VT_UI2:                  return VVT_SHORT;
    case VT_I4:
    case VT_UI4:
    case VT_INT:
    case VT_UINT:                 return VVT_INT;
    case VT_I8:
    case VT_UI8:                  return VVT_LONG;
    case VT_R4:                   return VVT_FLOAT;
    case VT_CY:
    case VT_DECIMAL:
    case VT_R8:                   return VVT_DOUBLE;
    case VT_DATE:                 return VVT_DATE;
    case VT_BSTR:                 return VVT_STR;
    case VT_UNKNOWN:
    case VT_DISPATCH:             return VVT_COM_DISPATCH;
    case VT_ERROR:                return VVT_ERROR;
    case VT_BOOL:                 return VVT_BOOL;

    case VT_I1 | VT_ARRAY:
    case VT_UI1 | VT_ARRAY:       return VVT_SBYTE_ARRAY;
    case VT_I2 | VT_ARRAY:
    case VT_UI2 | VT_ARRAY:       return VVT_SHORT_ARRAY;
    case VT_I4 | VT_ARRAY:
    case VT_UI4 | VT_ARRAY:
    case VT_INT | VT_ARRAY:
    case VT_UINT | VT_ARRAY:      return VVT_INT_ARRAY;
    case VT_I8 | VT_ARRAY:
    case VT_UI8 | VT_ARRAY:       return VVT_LONG_ARRAY;
    case VT_R4 | VT_ARRAY:        return VVT_FLOAT_ARRAY;
    case VT_CY | VT_ARRAY:
    case VT_DECIMAL | VT_ARRAY:
    case VT_R8 | VT_ARRAY:        return VVT_DOUBLE_ARRAY;
    case VT_DATE | VT_ARRAY:      return VVT_DATE_ARRAY;
    case VT_BSTR | VT_ARRAY:      return VVT_STR_ARRAY;
    case VT_UNKNOWN | VT_ARRAY:
    case VT_DISPATCH | VT_ARRAY:  return VVT_COM_DISPATCH_ARRAY;
    case VT_ERROR | VT_ARRAY:     return VVT_ERROR_ARRAY;
    case VT_BOOL | VT_ARRAY:      return VVT_BOOL_ARRAY;
    case VT_VARIANT | VT_ARRAY:   return VVT_VARIANT_ARRAY;

    default:  return VVT_UNKNOWN;
    }
}

BOOL_P CVolComVariant::ChangeType (const VOL_VARIANT_TYPE enNewType)
{
    static const VARTYPE cs_variant_types [] =
    {
        VT_EMPTY,
        VT_ERROR,
        VT_I1,
        VT_I2,
        VT_I4,
        VT_I8,
        VT_R4,
        VT_R8,
        VT_DATE,
        VT_BOOL,
        VT_BSTR,
        VT_UNKNOWN,
        VT_DISPATCH,

        VT_ERROR | VT_ARRAY,
        VT_I1 | VT_ARRAY,
        VT_I2 | VT_ARRAY,
        VT_I4 | VT_ARRAY,
        VT_I8 | VT_ARRAY,
        VT_R4 | VT_ARRAY,
        VT_R8 | VT_ARRAY,
        VT_DATE | VT_ARRAY,
        VT_BOOL | VT_ARRAY,
        VT_BSTR | VT_ARRAY,
        VT_UNKNOWN | VT_ARRAY,
        VT_DISPATCH | VT_ARRAY,
        VT_VARIANT | VT_ARRAY
    };
    COMPILE_TIME_ASSERT (NUM_ELEMENTS_OF (cs_variant_types) == _NUM_VOL_VARIANT_TYPES &&
            VVT_EMPTY == 0 &&
            VVT_ERROR == 1 &&
            VVT_SBYTE == 2 &&
            VVT_SHORT == 3 &&
            VVT_INT == 4 &&
            VVT_LONG == 5 &&
            VVT_FLOAT == 6 &&
            VVT_DOUBLE == 7 &&
            VVT_DATE == 8 &&
            VVT_BOOL == 9 &&
            VVT_STR == 10 &&
            VVT_COM_OBJECT == 11 &&
            VVT_COM_DISPATCH == 12 &&
            VVT_ERROR_ARRAY == 13 &&
            VVT_SBYTE_ARRAY == 14 &&
            VVT_SHORT_ARRAY == 15 &&
            VVT_INT_ARRAY == 16 &&
            VVT_LONG_ARRAY == 17 &&
            VVT_FLOAT_ARRAY == 18 &&
            VVT_DOUBLE_ARRAY == 19 &&
            VVT_DATE_ARRAY == 20 &&
            VVT_BOOL_ARRAY == 21 &&
            VVT_STR_ARRAY == 22 &&
            VVT_COM_OBJECT_ARRAY == 23 &&
            VVT_COM_DISPATCH_ARRAY == 24 &&
            VVT_VARIANT_ARRAY == 25 &&
            VVT_VARIANT_ARRAY + 1 == _NUM_VOL_VARIANT_TYPES);

    return (enNewType >= 0 && enNewType < _NUM_VOL_VARIANT_TYPES &&
            SUCCEEDED (::VariantChangeType (&m_var, &m_var, 0, cs_variant_types [enNewType])));
}

static INT_P sGetSafeArrayElementCount (SAFEARRAY* parray)
{
    ASSERT (parray != NULL);

    const INT_P npDimCount = (INT_P)::SafeArrayGetDim (parray);

    INT_P npElementCount = 0;
    long lLBound, lUBound;
    for (INT npDimIndex = 1; npDimIndex <= npDimCount; npDimIndex++)
    {
        SafeArrayGetLBound (parray, (INT)npDimIndex, &lLBound);
        SafeArrayGetUBound (parray, (INT)npDimIndex, &lUBound);

        const INT_P np = (INT_P)(lUBound + 1 - lLBound);  // 获得本维维数
        if (npElementCount == 0)
            npElementCount = np;
        else
            npElementCount *= np;
    }

    return npElementCount;
}

INT_P CVolComVariant::GetNumArrayElements () const
{
    SAFEARRAY* parray = GetSafeArray ();
    return (parray != NULL ? sGetSafeArrayElementCount (parray) : 0);
}

INT_P CVolComVariant::GetArrayElementSize () const
{
    SAFEARRAY* parray = GetSafeArray ();
    return (parray != NULL ? (INT_P)::SafeArrayGetElemsize (parray) : 0);
}

INT_P CVolComVariant::GetArrayDataSize () const
{
    SAFEARRAY* parray = GetSafeArray ();
    return (parray != NULL ? sGetSafeArrayElementCount (parray) * (INT_P)::SafeArrayGetElemsize (parray) : 0);
}

// pvarRes为一个未初始化的无数据VARIANT
BOOL_P CVolComVariant::GetValue (const INT_P npElementIndex, const VARTYPE vtReq, VARIANT* pvarRes) const
{
    ASSERT (vtReq != VT_EMPTY && (vtReq & VT_TYPEMASK) == vtReq && pvarRes != NULL);

    ::VariantInit (pvarRes);

    if ((m_var.vt & VT_ARRAY) != 0)  // 为数组数据?
    {
        if (npElementIndex < 0)  // 没有提供数组成员索引值?
        {
            if (vtReq == VT_VARIANT)
                return SUCCEEDED (VariantCopyInd (pvarRes, &m_var));
            
            return FALSE;
        }

        SAFEARRAY* parray = GetSafeArray ();

        BYTE HUGEP *pb;
        if (parray == NULL || FAILED (::SafeArrayAccessData (parray, (void HUGEP**)&pb)))
            return FALSE;
        ASSERT (npElementIndex < sGetSafeArrayElementCount (parray));  // 成员索引位置必须在有效范围内
        pb += npElementIndex * ::SafeArrayGetElemsize (parray);

        pvarRes->vt = (m_var.vt & VT_TYPEMASK);

        switch (pvarRes->vt)
        {
        case VT_I1:  pvarRes->cVal = *(CHAR*)pb;  break;
        case VT_I2:  pvarRes->iVal = *(SHORT*)pb;  break;
        case VT_I4:  pvarRes->lVal = *(LONG*)pb;  break;
        case VT_I8:  pvarRes->llVal = *(LONGLONG*)pb;  break;
        case VT_UI1:  pvarRes->bVal = *pb;  break;
        case VT_UI2:  pvarRes->uiVal = *(USHORT*)pb;  break;
        case VT_UI4:  pvarRes->ulVal = *(ULONG*)pb;  break;
        case VT_UI8:  pvarRes->ullVal = *(ULONGLONG*)pb;  break;
        case VT_INT:  pvarRes->intVal = *(INT*)pb;  break;
        case VT_UINT:  pvarRes->uintVal = *(UINT*)pb;  break;
        case VT_R4:  pvarRes->fltVal = *(FLOAT*)pb;  break;
        case VT_R8:  pvarRes->dblVal = *(DOUBLE*)pb;  break;
        case VT_BOOL:  pvarRes->boolVal = *(VARIANT_BOOL*)pb;  break;
        case VT_BSTR:  pvarRes->bstrVal = ::SysAllocString (*(BSTR*)pb);  break;
        case VT_CY:  pvarRes->cyVal = *(CY*)pb;  break;
        case VT_DATE:  pvarRes->date = *(DATE*)pb;  break;
        case VT_DECIMAL:  pvarRes->decVal = *(DECIMAL*)pb;  break;
        case VT_UNKNOWN:  pvarRes->punkVal = *(IUnknown**)pb; if (pvarRes->punkVal != NULL) pvarRes->punkVal->AddRef (); break;
        case VT_DISPATCH:  pvarRes->pdispVal = *(IDispatch**)pb; if (pvarRes->pdispVal != NULL) pvarRes->pdispVal->AddRef (); break;
        case VT_ERROR:  pvarRes->scode = *(SCODE*)pb;  break;
        case VT_VARIANT:  if (FAILED (::VariantCopyInd (pvarRes, (VARIANT*)pb))) pb = NULL;  break;
        default:  pb = NULL;  break;
        }

        ::SafeArrayUnaccessData (parray);

        if (pb == NULL)
            return FALSE;
    }
    else
    {
        if (npElementIndex >= 0 ||  // 提供了数组成员索引值?
                FAILED (VariantCopyInd (pvarRes, &m_var)))
        {
            return FALSE;
        }
    }

    if (vtReq != VT_VARIANT)
    {
        if (pvarRes->vt != vtReq &&
                FAILED (VariantChangeType (pvarRes, pvarRes, 0, vtReq)))
        {
            VariantClear (pvarRes);
            return FALSE;
        }
    }

    return TRUE;
}

S_BYTE CVolComVariant::GetValue_S_BYTE (const INT_P npElementIndex) const
{
    VARIANT varRes;
    return (GetValue (npElementIndex, VT_I1, &varRes) == FALSE ? 0 : varRes.cVal);
}

SHORT CVolComVariant::GetValue_SHORT (const INT_P npElementIndex) const
{
    VARIANT varRes;
    return (GetValue (npElementIndex, VT_I2, &varRes) == FALSE ? 0 : varRes.iVal);
}

TCHAR CVolComVariant::GetValue_TCHAR (const INT_P npElementIndex) const
{
    COMPILE_TIME_ASSERT (sizeof (TCHAR) == sizeof (SHORT));
    return (TCHAR)GetValue_SHORT (npElementIndex);
}

INT CVolComVariant::GetValue_INT (const INT_P npElementIndex) const
{
    VARIANT varRes;
    return (GetValue (npElementIndex, VT_I4, &varRes) == FALSE ? 0 : varRes.lVal);
}

INT64 CVolComVariant::GetValue_INT64 (const INT_P npElementIndex) const
{
    VARIANT varRes;
    return (GetValue (npElementIndex, VT_I8, &varRes) == FALSE ? 0 : (INT64)varRes.llVal);
}

FLOAT CVolComVariant::GetValue_FLOAT (const INT_P npElementIndex) const
{
    VARIANT varRes;
    return (GetValue (npElementIndex, VT_R4, &varRes) == FALSE ? 0 : varRes.fltVal);
}

DOUBLE CVolComVariant::GetValue_DOUBLE (const INT_P npElementIndex) const
{
    VARIANT varRes;
    return (GetValue (npElementIndex, VT_R8, &varRes) == FALSE ? 0 : varRes.dblVal);
}

BOOL CVolComVariant::GetValue_BOOL (const INT_P npElementIndex) const
{
    VARIANT varRes;
    return (GetValue (npElementIndex, VT_BOOL, &varRes) == FALSE ? FALSE : (varRes.boolVal != 0));
}

CVolString CVolComVariant::GetValue_CVolString (const INT_P npElementIndex) const
{
    CVolString value;

    VARIANT varRes;
    if (GetValue (npElementIndex, VT_BSTR, &varRes))
    {
        value.SetText (varRes.bstrVal);
        VariantClear (&varRes);
    }

    return value;
}

CVolComVariant& CVolComVariant::GetRecordField (const TCHAR* szFieldName, CVolComVariant& vValue) const
{
    vValue.Clear ();

    if (m_var.vt == VT_RECORD && m_var.pRecInfo != NULL && m_var.pvRecord != NULL)
        m_var.pRecInfo->GetField (m_var.pvRecord, szFieldName, &vValue.m_var);

    return vValue;
}

CVolObject& CVolComVariant::GetVolObject (const INT_P npElementIndex, CVolRuntimeClass* pRuntimeClass, CVolObjectDestroyer& objDestroyer) const
{
    ASSERT (pRuntimeClass != NULL);

    VARIANT varRes;
    if (GetValue (npElementIndex, VT_UNKNOWN, &varRes) == FALSE)
        return CVolComRecordObject::sGetVolObject (NULL, pRuntimeClass, objDestroyer);

    CVolObject& obj = CVolComRecordObject::sGetVolObject (varRes.punkVal, pRuntimeClass, objDestroyer);

    VariantClear (&varRes);
    return obj;
}

BOOL_P CVolComVariant::GetBin (CVolMem* pVolMem)
{
    ASSERT (pVolMem != NULL);

    pVolMem->Empty ();

    if (m_var.vt == VT_RECORD)
    {
        ULONG ulSize = 0;
        if (m_var.pRecInfo != NULL && m_var.pvRecord != NULL &&
                SUCCEEDED (m_var.pRecInfo->GetSize (&ulSize)))
        {
            pVolMem->CopyFrom (m_var.pvRecord, (INT)ulSize);
            return TRUE;
        }

        return FALSE;
    }

    SAFEARRAY* parray = GetSafeArray ();
    if (parray == NULL)
        return FALSE;

    const VARTYPE vtElement = (m_var.vt & VT_TYPEMASK);

    if (vtElement == VT_UI1 || vtElement == VT_I1 ||
            vtElement == VT_UI2 || vtElement == VT_I2 ||
            vtElement == VT_UI4 || vtElement == VT_I4 ||
            vtElement == VT_UI8 || vtElement == VT_I8 ||
            vtElement == VT_UINT || vtElement == VT_INT ||
            vtElement == VT_R4 || vtElement == VT_R8 || vtElement == VT_BOOL ||
            vtElement == VT_DATE || vtElement == VT_ERROR ||
            vtElement == VT_DECIMAL || vtElement == VT_CY)
    {
        BYTE HUGEP *pb;
        if (SUCCEEDED (::SafeArrayAccessData (parray, (void HUGEP**)&pb)))
        {
            pVolMem->CopyFrom (pb, sGetSafeArrayElementCount (parray) * ::SafeArrayGetElemsize (parray));
            ::SafeArrayUnaccessData (parray);
            return TRUE;
        }
    }

    return FALSE;
}

BOOL_P CVolComVariant::GetComObject (CVolComObject* pVolComObject, const INT_P npElementIndex)
{
    ASSERT (pVolComObject != NULL);

    VARIANT varRes;
    if (GetValue (npElementIndex, VT_UNKNOWN, &varRes) == FALSE)
        return FALSE;

    pVolComObject->SetUnknownObject (varRes.punkVal);
    VariantClear (&varRes);
    return TRUE;
}

CVolComObject& CVolComVariant::GetComObject2 (CVolComObject& objVolCom, const INT_P npElementIndex)
{
    VARIANT varRes;
    if (GetValue (npElementIndex, VT_UNKNOWN, &varRes))
    {
        objVolCom.SetUnknownObject (varRes.punkVal);
        VariantClear (&varRes);
    }
    else
        objVolCom.ReleaseUnknownObject ();

    return objVolCom;
}

INT_P CVolComVariant::GetArray (void* pBuf, INT_P npNumReadElements, INT_P npFirstReadElementIndex, const INT_P npElementSize) const
{
    ASSERT (npFirstReadElementIndex >= 0 && npElementSize > 0);
    ASSERT_RW_ADR (pBuf, npNumReadElements * npElementSize);

    if (npFirstReadElementIndex < 0 || npNumReadElements <= 0)
        return 0;

    SAFEARRAY* parray = GetSafeArray ();
    if (parray != NULL)
    {
        ASSERT ((INT_P)::SafeArrayGetElemsize (parray) == npElementSize);  // 进入本方法的前提

        BYTE HUGEP *pb;
        if (SUCCEEDED (::SafeArrayAccessData (parray, (void HUGEP**)&pb)))
        {
            INT_P npNumRealReadElements = sGetSafeArrayElementCount (parray) - npFirstReadElementIndex;
            npNumRealReadElements = CLIP (npNumRealReadElements, 0, npNumReadElements);

            if (npNumRealReadElements > 0)
                COPY_MEM (pBuf, pb + npFirstReadElementIndex * npElementSize, npNumRealReadElements * npElementSize);

            ::SafeArrayUnaccessData (parray);
            return npNumRealReadElements;
        }
    }

    return 0;
}

static INT_P sGetNumReadElements (const INT_P npMaxNumBufElements, const INT_P npNumReadElements)
{
    ASSERT (npMaxNumBufElements >= 0);

    if (npNumReadElements < 0)  // 使用最大允许尺寸?
        return npMaxNumBufElements;
    
    if (npNumReadElements > npMaxNumBufElements)
        return npMaxNumBufElements;

    return npNumReadElements;
}

INT_P CVolComVariant::GetArray_S_BYTE (S_BYTE* pBuf, const INT_P npMaxNumBufElements, INT_P npFirstReadElementIndex, INT_P npNumReadElements) const
{
    const VARTYPE vtElement = (m_var.vt & VT_TYPEMASK);
    if (vtElement != VT_UI1 && vtElement != VT_I1)
        return 0;

    return GetArray (pBuf, sGetNumReadElements (npMaxNumBufElements, npNumReadElements), npFirstReadElementIndex, sizeof (S_BYTE));
}

INT_P CVolComVariant::GetArray_SHORT (SHORT* pBuf, const INT_P npMaxNumBufElements, INT_P npFirstReadElementIndex, INT_P npNumReadElements) const
{
    const VARTYPE vtElement = (m_var.vt & VT_TYPEMASK);
    if (vtElement != VT_UI2 && vtElement != VT_I2)
        return 0;

    return GetArray (pBuf, sGetNumReadElements (npMaxNumBufElements, npNumReadElements), npFirstReadElementIndex, sizeof (SHORT));
}

INT_P CVolComVariant::GetArray_TCHAR (TCHAR* pBuf, const INT_P npMaxNumBufElements, INT_P npFirstReadElementIndex, INT_P npNumReadElements) const
{
    COMPILE_TIME_ASSERT (sizeof (TCHAR) == sizeof (SHORT));
    return GetArray_SHORT ((SHORT*)pBuf, npMaxNumBufElements, npFirstReadElementIndex, npNumReadElements);
}

INT_P CVolComVariant::GetArray_INT (INT* pBuf, const INT_P npMaxNumBufElements, INT_P npFirstReadElementIndex, INT_P npNumReadElements) const
{
    const VARTYPE vtElement = (m_var.vt & VT_TYPEMASK);
    if (vtElement != VT_UI4 && vtElement != VT_I4 && vtElement != VT_INT && vtElement != VT_UINT)
        return 0;

    return GetArray (pBuf, sGetNumReadElements (npMaxNumBufElements, npNumReadElements), npFirstReadElementIndex, sizeof (INT));
}

INT_P CVolComVariant::GetArray_INT64 (INT64* pBuf, const INT_P npMaxNumBufElements, INT_P npFirstReadElementIndex, INT_P npNumReadElements) const
{
    const VARTYPE vtElement = (m_var.vt & VT_TYPEMASK);
    if (vtElement != VT_UI8 && vtElement != VT_I8)
        return 0;

    return GetArray (pBuf, sGetNumReadElements (npMaxNumBufElements, npNumReadElements), npFirstReadElementIndex, sizeof (INT64));
}

INT_P CVolComVariant::GetArray_FLOAT (FLOAT* pBuf, const INT_P npMaxNumBufElements, INT_P npFirstReadElementIndex, INT_P npNumReadElements) const
{
    ASSERT (npMaxNumBufElements >= 0 && npFirstReadElementIndex >= 0);

    npNumReadElements = sGetNumReadElements (npMaxNumBufElements, npNumReadElements);
    ASSERT_RW_ADR (pBuf, npNumReadElements * sizeof (FLOAT));

    if (npFirstReadElementIndex < 0 || npNumReadElements <= 0)
        return 0;

    const VARTYPE vtElement = (m_var.vt & VT_TYPEMASK);

    if (vtElement == VT_R4 || vtElement == VT_R8 || vtElement == VT_DATE)
    {
        SAFEARRAY* parray = GetSafeArray ();

        BYTE HUGEP *pb;
        if (parray != NULL && SUCCEEDED (::SafeArrayAccessData (parray, (void HUGEP**)&pb)))
        {
            INT_P npNumRealReadElements = sGetSafeArrayElementCount (parray) - npFirstReadElementIndex;
            npNumRealReadElements = CLIP (npNumRealReadElements, 0, npNumReadElements);

            if (vtElement == VT_R4)
            {
                ASSERT (::SafeArrayGetElemsize (parray) == sizeof (FLOAT));

                if (npNumRealReadElements > 0)
                    COPY_MEM (pBuf, pb + npFirstReadElementIndex * sizeof (FLOAT), npNumRealReadElements * sizeof (FLOAT));
            }
            else
            {
                COMPILE_TIME_ASSERT (sizeof (DATE) == sizeof (DOUBLE));

                ASSERT (::SafeArrayGetElemsize (parray) == sizeof (DOUBLE));
                const DOUBLE* pdbSource = (const DOUBLE*)pb + npFirstReadElementIndex;

                for (INT_P npIndex = 0; npIndex < npNumRealReadElements; npIndex++, pdbSource++, pBuf++)
                    *pBuf = (FLOAT)*pdbSource;
            }

            ::SafeArrayUnaccessData (parray);
            return npNumRealReadElements;
        }
    }

    return 0;
}

INT_P CVolComVariant::GetArray_DOUBLE (DOUBLE* pBuf, const INT_P npMaxNumBufElements, INT_P npFirstReadElementIndex, INT_P npNumReadElements) const
{
    ASSERT (npMaxNumBufElements >= 0 && npFirstReadElementIndex >= 0);

    npNumReadElements = sGetNumReadElements (npMaxNumBufElements, npNumReadElements);
    ASSERT_RW_ADR (pBuf, npNumReadElements * sizeof (DOUBLE));

    if (npFirstReadElementIndex < 0 || npNumReadElements <= 0)
        return 0;

    const VARTYPE vtElement = (m_var.vt & VT_TYPEMASK);

    if (vtElement == VT_R4 || vtElement == VT_R8 || vtElement == VT_DATE)
    {
        SAFEARRAY* parray = GetSafeArray ();

        BYTE HUGEP *pb;
        if (parray != NULL && SUCCEEDED (::SafeArrayAccessData (parray, (void HUGEP**)&pb)))
        {
            INT_P npNumRealReadElements = sGetSafeArrayElementCount (parray) - npFirstReadElementIndex;
            npNumRealReadElements = CLIP (npNumRealReadElements, 0, npNumReadElements);

            if (vtElement != VT_R4)
            {
                COMPILE_TIME_ASSERT (sizeof (DATE) == sizeof (DOUBLE));
                ASSERT (::SafeArrayGetElemsize (parray) == sizeof (DOUBLE));

                if (npNumRealReadElements > 0)
                    COPY_MEM (pBuf, pb + npFirstReadElementIndex * sizeof (DOUBLE), npNumRealReadElements * sizeof (DOUBLE));
            }
            else
            {
                ASSERT (::SafeArrayGetElemsize (parray) == sizeof (FLOAT));
                const FLOAT* pftSource = (const FLOAT*)pb + npFirstReadElementIndex;

                for (INT_P npIndex = 0; npIndex < npNumRealReadElements; npIndex++, pftSource++, pBuf++)
                    *pBuf = (DOUBLE)*pftSource;
            }

            ::SafeArrayUnaccessData (parray);
            return npNumRealReadElements;
        }
    }

    return 0;
}

INT_P CVolComVariant::GetArray_BOOL (BOOL* pBuf, const INT_P npMaxNumBufElements, INT_P npFirstReadElementIndex, INT_P npNumReadElements) const
{
    ASSERT (npMaxNumBufElements >= 0 && npFirstReadElementIndex >= 0);

    npNumReadElements = sGetNumReadElements (npMaxNumBufElements, npNumReadElements);
    ASSERT_RW_ADR (pBuf, npNumReadElements * sizeof (BOOL));

    if (npFirstReadElementIndex < 0 || npNumReadElements <= 0)
        return 0;

    if ((m_var.vt & VT_TYPEMASK) == VT_BOOL)
    {
        SAFEARRAY* parray = GetSafeArray ();

        BYTE HUGEP *pb;
        if (parray != NULL && SUCCEEDED (::SafeArrayAccessData (parray, (void HUGEP**)&pb)))
        {
            INT_P npNumRealReadElements = sGetSafeArrayElementCount (parray) - npFirstReadElementIndex;
            npNumRealReadElements = CLIP (npNumRealReadElements, 0, npNumReadElements);

            ASSERT (::SafeArrayGetElemsize (parray) == sizeof (VARIANT_BOOL));
            const VARIANT_BOOL* pblSource = (const VARIANT_BOOL*)pb + npFirstReadElementIndex;

            for (INT_P npIndex = 0; npIndex < npNumRealReadElements; npIndex++, pblSource++, pBuf++)
                *pBuf = (*pblSource != 0);

            ::SafeArrayUnaccessData (parray);
            return npNumRealReadElements;
        }
    }

    return 0;
}

INT_P CVolComVariant::GetArray_CVolString (CVolString* pBuf, const INT_P npMaxNumBufElements, INT_P npFirstReadElementIndex, INT_P npNumReadElements) const
{
    ASSERT (npMaxNumBufElements >= 0 && npFirstReadElementIndex >= 0);

    npNumReadElements = sGetNumReadElements (npMaxNumBufElements, npNumReadElements);
    ASSERT_RW_ADR (pBuf, npNumReadElements * sizeof (CVolString));

    if (npFirstReadElementIndex < 0 || npNumReadElements <= 0)
        return 0;

    if ((m_var.vt & VT_TYPEMASK) == VT_BSTR)
    {
        SAFEARRAY* parray = GetSafeArray ();

        BYTE HUGEP *pb;
        if (parray != NULL && SUCCEEDED (::SafeArrayAccessData (parray, (void HUGEP**)&pb)))
        {
            INT_P npNumRealReadElements = sGetSafeArrayElementCount (parray) - npFirstReadElementIndex;
            npNumRealReadElements = CLIP (npNumRealReadElements, 0, npNumReadElements);

            ASSERT (::SafeArrayGetElemsize (parray) == sizeof (BSTR));
            const BSTR* pbstrSource = (const BSTR*)pb + npFirstReadElementIndex;

            for (INT_P npIndex = 0; npIndex < npNumRealReadElements; npIndex++, pbstrSource++, pBuf++)
                pBuf->SetText (*pbstrSource);

            ::SafeArrayUnaccessData (parray);
            return npNumRealReadElements;
        }
    }

    return 0;
}

INT_P CVolComVariant::GetArray_Variant (CVolComVariant* pBuf, const INT_P npMaxNumBufElements, INT_P npFirstReadElementIndex, INT_P npNumReadElements) const
{
    ASSERT (npMaxNumBufElements >= 0 && npFirstReadElementIndex >= 0);

    npNumReadElements = sGetNumReadElements (npMaxNumBufElements, npNumReadElements);
    ASSERT_RW_ADR (pBuf, npNumReadElements * sizeof (CVolComVariant));

    if (npFirstReadElementIndex < 0 || npNumReadElements <= 0)
        return 0;

    if ((m_var.vt & VT_TYPEMASK) == VT_VARIANT)
    {
        SAFEARRAY* parray = GetSafeArray ();

        BYTE HUGEP *pb;
        if (parray != NULL && SUCCEEDED (::SafeArrayAccessData (parray, (void HUGEP**)&pb)))
        {
            INT_P npNumRealReadElements = sGetSafeArrayElementCount (parray) - npFirstReadElementIndex;
            npNumRealReadElements = CLIP (npNumRealReadElements, 0, npNumReadElements);

            ASSERT (::SafeArrayGetElemsize (parray) == sizeof (VARIANT));
            const VARIANT* pvSource = (const VARIANT*)pb + npFirstReadElementIndex;

            for (INT_P npIndex = 0; npIndex < npNumRealReadElements; npIndex++, pvSource++, pBuf++)
                ::VariantCopy (&pBuf->m_var, pvSource);

            ::SafeArrayUnaccessData (parray);
            return npNumRealReadElements;
        }
    }

    return 0;
}

INT_P CVolComVariant::GetArray_ComObject (CVolComObject* pBuf, const INT_P npMaxNumBufElements, INT_P npFirstReadElementIndex, INT_P npNumReadElements) const
{
    ASSERT (npMaxNumBufElements >= 0 && npFirstReadElementIndex >= 0);

    npNumReadElements = sGetNumReadElements (npMaxNumBufElements, npNumReadElements);
    ASSERT_RW_ADR (pBuf, npNumReadElements * sizeof (CVolComObject));

    if (npFirstReadElementIndex < 0 || npNumReadElements <= 0)
        return 0;

    const VARTYPE vt = (m_var.vt & VT_TYPEMASK);
    if (vt == VT_UNKNOWN || vt == VT_DISPATCH)
    {
        SAFEARRAY* parray = GetSafeArray ();

        BYTE HUGEP *pb;
        if (parray != NULL && SUCCEEDED (::SafeArrayAccessData (parray, (void HUGEP**)&pb)))
        {
            INT_P npNumRealReadElements = sGetSafeArrayElementCount (parray) - npFirstReadElementIndex;
            npNumRealReadElements = CLIP (npNumRealReadElements, 0, npNumReadElements);

            ASSERT (::SafeArrayGetElemsize (parray) == sizeof (VARIANT));
            IUnknown** ppobjSource = (IUnknown**)pb + npFirstReadElementIndex;

            for (INT_P npIndex = 0; npIndex < npNumRealReadElements; npIndex++, ppobjSource++, pBuf++)
                pBuf->SetUnknownObject (*ppobjSource);

            ::SafeArrayUnaccessData (parray);
            return npNumRealReadElements;
        }
    }

    return 0;
}

BYTE* CVolComVariant::LockArray ()
{
    SAFEARRAY* parray = GetSafeArray ();
    BYTE HUGEP *pb;
    return (parray != NULL && SUCCEEDED (::SafeArrayAccessData (parray, (void HUGEP**)&pb)) ? pb : NULL);
}

void CVolComVariant::UnlockArray ()
{
    SAFEARRAY* parray = GetSafeArray ();
    if (parray != NULL)
        ::SafeArrayUnaccessData (parray);
}

// pvarNew交由本方法进行清理
BOOL_P CVolComVariant::SetValue (VARIANT* pvarNew, const INT_P npElementIndex)
{
    ASSERT (pvarNew != NULL && pvarNew->vt != VT_EMPTY);

    BOOL_P blpSucceeded = FALSE;
    const VARTYPE vtElement = (m_var.vt & VT_TYPEMASK);

    do
    {
        if ((m_var.vt & VT_ARRAY) != 0)  // 为数组数据?
        {
            if (npElementIndex < 0)  // 没有提供数组成员索引值?
                break;

            if (vtElement != VT_VARIANT && vtElement != pvarNew->vt)
            {
                if (FAILED (VariantChangeType (pvarNew, pvarNew, 0, vtElement)))  // 转换类型失败?
                    break;
            }

            SAFEARRAY* parray = GetSafeArray ();

            BYTE HUGEP *pb;
            if (parray == NULL || FAILED (::SafeArrayAccessData (parray, (void HUGEP**)&pb)))
                break;
            ASSERT (npElementIndex < sGetSafeArrayElementCount (parray));  // 成员索引位置必须在有效范围内
            pb += npElementIndex * ::SafeArrayGetElemsize (parray);

            blpSucceeded = TRUE;
            switch (vtElement)
            {
            case VT_I1:  *(CHAR*)pb = pvarNew->cVal;  break;
            case VT_I2:  *(SHORT*)pb = pvarNew->iVal;  break;
            case VT_I4:  *(LONG*)pb = pvarNew->lVal;  break;
            case VT_I8:  *(LONGLONG*)pb = pvarNew->llVal;  break;
            case VT_UI1:  *pb = pvarNew->bVal;  break;
            case VT_UI2:  *(USHORT*)pb = pvarNew->uiVal;  break;
            case VT_UI4:  *(ULONG*)pb = pvarNew->ulVal;  break;
            case VT_UI8:  *(ULONGLONG*)pb = pvarNew->ullVal;  break;
            case VT_INT:  *(INT*)pb = pvarNew->intVal;  break;
            case VT_UINT:  *(UINT*)pb = pvarNew->uintVal;  break;
            case VT_R4:  *(FLOAT*)pb = pvarNew->fltVal;  break;
            case VT_R8:  *(DOUBLE*)pb = pvarNew->dblVal;  break;
            case VT_BOOL:  *(VARIANT_BOOL*)pb = pvarNew->boolVal;  break;
            case VT_CY:  *(CY*)pb = pvarNew->cyVal;  break;
            case VT_DATE:  *(DATE*)pb = pvarNew->date;  break;
            case VT_DECIMAL:  *(DECIMAL*)pb = pvarNew->decVal;  break;
            case VT_ERROR:  *(SCODE*)pb = pvarNew->scode;  break;
            case VT_VARIANT:
                ::VariantClear ((VARIANT*)pb);
                ::VariantCopyInd ((VARIANT*)pb, pvarNew);
                break;
            case VT_BSTR:
                if (*(BSTR*)pb != NULL)
                    ::SysFreeString (*(BSTR*)pb);
                *(BSTR*)pb = ::SysAllocString (pvarNew->bstrVal);
                break;
            case VT_UNKNOWN:
                if (*(IUnknown**)pb != NULL)
                    (*(IUnknown**)pb)->Release ();
                *(IUnknown**)pb = pvarNew->punkVal;
                if (pvarNew->punkVal != NULL)
                    pvarNew->punkVal->AddRef ();
                break;
            case VT_DISPATCH:
                if (*(IDispatch**)pb != NULL)
                    (*(IDispatch**)pb)->Release ();
                *(IDispatch**)pb = pvarNew->pdispVal;
                if (pvarNew->pdispVal != NULL)
                    pvarNew->pdispVal->AddRef ();
                break;
            default:
                blpSucceeded = FALSE;
                break;
            }

            ::SafeArrayUnaccessData (parray);
        }
        else
        {
            if (npElementIndex >= 0)  // 提供了数组成员索引值?
                break;

            if ((m_var.vt & VT_BYREF) != 0 &&
                    SUCCEEDED (VariantChangeType (pvarNew, pvarNew, 0, vtElement)))  // 转换类型成功?
            {
                blpSucceeded = TRUE;

                switch (vtElement)
                {
                case VT_I1:  *m_var.pcVal = pvarNew->cVal;  break;
                case VT_I2:  *m_var.piVal = pvarNew->iVal;  break;
                case VT_I4:  *m_var.plVal = pvarNew->lVal;  break;
                case VT_I8:  *m_var.pllVal = pvarNew->llVal;  break;
                case VT_UI1:  *m_var.pbVal = pvarNew->bVal;  break;
                case VT_UI2:  *m_var.puiVal = pvarNew->uiVal;  break;
                case VT_UI4:  *m_var.pulVal = pvarNew->ulVal;  break;
                case VT_UI8:  *m_var.pullVal = pvarNew->ullVal;  break;
                case VT_INT:  *m_var.pintVal = pvarNew->intVal;  break;
                case VT_UINT:  *m_var.puintVal = pvarNew->uintVal;  break;
                case VT_R4:  *m_var.pfltVal = pvarNew->fltVal;  break;
                case VT_R8:  *m_var.pdblVal = pvarNew->dblVal;  break;
                case VT_BOOL:  *m_var.pboolVal = pvarNew->boolVal;  break;
                case VT_CY:  *m_var.pcyVal = pvarNew->cyVal;  break;
                case VT_DATE:  *m_var.pdate = pvarNew->date;  break;
                case VT_DECIMAL:  *m_var.pdecVal = pvarNew->decVal;  break;
                case VT_ERROR:  *m_var.pscode = pvarNew->scode;  break;
                case VT_VARIANT:  ::VariantCopyInd (m_var.pvarVal, pvarNew);  break;
                case VT_BSTR:
                    if (*m_var.pbstrVal != NULL)
                        ::SysFreeString (*m_var.pbstrVal);
                    *m_var.pbstrVal = ::SysAllocString (pvarNew->bstrVal);
                    break;
                case VT_UNKNOWN:
                    if (*m_var.ppunkVal != NULL)
                        (*m_var.ppunkVal)->Release ();
                    *m_var.ppunkVal = pvarNew->punkVal;
                    if (pvarNew->punkVal != NULL)
                        pvarNew->punkVal->AddRef ();
                    break;
                case VT_DISPATCH:
                    if (*m_var.ppdispVal != NULL)
                        (*m_var.ppdispVal)->Release ();
                    *m_var.ppdispVal = pvarNew->pdispVal;
                    if (pvarNew->pdispVal != NULL)
                        pvarNew->pdispVal->AddRef ();
                    break;
                default:
                    blpSucceeded = FALSE;
                    break;
                }
            }

            if (blpSucceeded == FALSE)
                blpSucceeded = SUCCEEDED (::VariantCopyInd (&m_var, pvarNew));
        }
    }
    while (FALSE);

    VariantClear (pvarNew);
    return blpSucceeded;
}

BOOL_P CVolComVariant::Set_S_BYTE (const S_BYTE value, const INT_P npElementIndex)
{
    VARIANT var;
    var.vt = VT_I1;
    var.cVal = value;
    return SetValue (&var, npElementIndex);
}

BOOL_P CVolComVariant::Set_SHORT (const SHORT value, const INT_P npElementIndex)
{
    VARIANT var;
    var.vt = VT_I2;
    var.iVal = value;
    return SetValue (&var, npElementIndex);
}

BOOL_P CVolComVariant::Set_TCHAR (const TCHAR value, const INT_P npElementIndex)
{
    COMPILE_TIME_ASSERT (sizeof (SHORT) == sizeof (TCHAR));
    return Set_SHORT ((SHORT)value, npElementIndex);
}

BOOL_P CVolComVariant::Set_INT (const INT value, const INT_P npElementIndex)
{
    VARIANT var;
    var.vt = VT_I4;
    var.lVal = value;
    return SetValue (&var, npElementIndex);
}

BOOL_P CVolComVariant::Set_INT64 (const INT64 value, const INT_P npElementIndex)
{
    VARIANT var;
    var.vt = VT_I8;
    var.llVal = value;
    return SetValue (&var, npElementIndex);
}

BOOL_P CVolComVariant::Set_FLOAT (const FLOAT value, const INT_P npElementIndex)
{
    VARIANT var;
    var.vt = VT_R4;
    var.fltVal = value;
    return SetValue (&var, npElementIndex);
}

BOOL_P CVolComVariant::Set_DOUBLE (const DOUBLE value, const INT_P npElementIndex)
{
    VARIANT var;
    var.vt = VT_R8;
    var.dblVal = value;
    return SetValue (&var, npElementIndex);
}

BOOL_P CVolComVariant::Set_BOOL (const BOOL value, const INT_P npElementIndex)
{
    VARIANT var;
    var.vt = VT_BOOL;
    var.boolVal = (value ? -1 : 0);
    return SetValue (&var, npElementIndex);
}

BOOL_P CVolComVariant::Set_CVolString (const TCHAR* value, const INT_P npElementIndex)
{
    VARIANT var;
    var.vt = VT_BSTR;
    var.bstrVal = ::SysAllocString (value);
    return SetValue (&var, npElementIndex);
}

BOOL_P CVolComVariant::SetComObject (IUnknown* pComObject, const INT_P npElementIndex)
{
    VARIANT var;
    var.vt = VT_UNKNOWN;
    var.punkVal = pComObject;
    if (pComObject != NULL)
        pComObject->AddRef ();

    return SetValue (&var, npElementIndex);
}

BOOL_P CVolComVariant::SetComDispatchObject (IUnknown* pComObject, const INT_P npElementIndex)
{
    IDispatch* pDispatch;
    if (pComObject != NULL &&
            SUCCEEDED (pComObject->QueryInterface (IID_IDispatch, (LPVOID*)&pDispatch)))
    {
        ASSERT (pDispatch != NULL);
    }
    else
        pDispatch = NULL;

    VARIANT var;
    var.vt = VT_DISPATCH;
    var.pdispVal = pDispatch;

    return SetValue (&var, npElementIndex);
}

BOOL_P CVolComVariant::SetVolObject (CVolObject* pVolObject, const INT_P npElementIndex)
{
    ASSERT (pVolObject != NULL);

    VARIANT var;
    var.vt = VT_UNKNOWN;
    var.punkVal = CVolComRecordObject::sCreateNew (pVolObject);

    return SetValue (&var, npElementIndex);
}

BOOL_P CVolComVariant::SetVariant (const VARIANT* pVar, const INT_P npElementIndex)
{
    VARIANT var;
    VariantInit (&var);
    VariantCopyInd (&var, pVar);

    return SetValue (&var, npElementIndex);
}

BOOL_P CVolComVariant::CreateEmptyArray (const VOL_NEW_VARY_ELEMENT_TYPE enType, const INT_P npNumElements)
{
    ASSERT (npNumElements >= 0);

    if (npNumElements < 0 || enType < 0 || enType >= _NUM_VOL_NEW_VARY_ELEMENT_TYPES)
        return FALSE;

    static const VARTYPE cs_element_vtypes [] =
    {
        VT_ERROR,
        VT_UI1,  // 很多外部库字节集数据只识别此类型
        VT_I2,
        VT_I4,
        VT_I8,
        VT_R4,
        VT_R8,
        VT_DATE,
        VT_BOOL,
        VT_BSTR,
        VT_UNKNOWN,
        VT_DISPATCH,
        VT_VARIANT
    };
    COMPILE_TIME_ASSERT (NUM_ELEMENTS_OF (cs_element_vtypes) == _NUM_VOL_NEW_VARY_ELEMENT_TYPES &&
            VNET_ERROR == 0 &&
            VNET_SBYTE == 1 &&
            VNET_SHORT == 2 &&
            VNET_INT == 3 &&
            VNET_LONG == 4 &&
            VNET_FLOAT == 5 &&
            VNET_DOUBLE == 6 &&
            VNET_DATE == 7 &&
            VNET_BOOL == 8 &&
            VNET_STR == 9 &&
            VNET_COM_OBJECT == 10 &&
            VNET_COM_DISPATCH == 11 &&
            VNET_VARIANT == 12 &&
            VNET_VARIANT + 1 == _NUM_VOL_NEW_VARY_ELEMENT_TYPES);

    SAFEARRAYBOUND aryDim;
    aryDim.lLbound = 0;  // aryDim.lLbound = 1;
    aryDim.cElements = (ULONG)npNumElements;

    const VARTYPE vt = cs_element_vtypes [enType];
    SAFEARRAY* parray = ::SafeArrayCreate (vt, 1, &aryDim);
    if (parray != NULL)
    {
        ::VariantClear (&m_var);
        m_var.vt = (vt | VT_ARRAY);
        m_var.parray = parray;
        return TRUE;
    }

    return FALSE;
}

BOOL_P CVolComVariant::CreateArray (const VOL_NEW_VARY_ELEMENT_TYPE enType, const void* pData, const INT_P npNumElements, const INT_P npElementSize)
{
    ASSERT_R_ADR (pData, npNumElements * npElementSize);

    if (CreateEmptyArray (enType, npNumElements) == FALSE)
        return FALSE;

    ASSERT (m_var.parray != NULL && npNumElements >= 0 &&  // CreateEmptyArray中算法决定
            sGetSafeArrayElementCount (m_var.parray) == npNumElements &&
            (INT_P)::SafeArrayGetElemsize (m_var.parray) == npElementSize);
    
    if (npNumElements == 0)
        return TRUE;

    BYTE HUGEP *pb;
    if (SUCCEEDED (::SafeArrayAccessData (m_var.parray, (void HUGEP**)&pb)))
    {
        COPY_MEM (pb, pData, npNumElements * npElementSize);
        ::SafeArrayUnaccessData (m_var.parray);
        return TRUE;
    }

    return FALSE;
}

BOOL_P CVolComVariant::CreateByteArrayFromData (const void* pData, const INT_P npDataSize)
{
    return CreateArray (VNET_SBYTE, pData, npDataSize, sizeof (S_BYTE));
}

static INT_P sGetNumWriteElements (const INT_P npMaxNumElements, const INT_P npFirstWriteElementIndex, const INT_P npNumWriteElements)
{
    ASSERT (npMaxNumElements >= 0 && npFirstWriteElementIndex >= 0);

    const INT_P npNumBehindElements = npMaxNumElements - npFirstWriteElementIndex;
    return ((npNumWriteElements < 0 || npNumWriteElements > npNumBehindElements) ? npNumBehindElements : npNumWriteElements);
}

BOOL_P CVolComVariant::CreateArray_S_BYTE (const S_BYTE* pData, const INT_P npMaxNumElements, INT_P npFirstWriteElementIndex, INT_P npNumWriteElements)
{
    return CreateArray (VNET_SBYTE, pData + npFirstWriteElementIndex,
            sGetNumWriteElements (npMaxNumElements, npFirstWriteElementIndex, npNumWriteElements), sizeof (S_BYTE));
}

BOOL_P CVolComVariant::CreateArray_SHORT (const SHORT* pData, const INT_P npMaxNumElements, INT_P npFirstWriteElementIndex, INT_P npNumWriteElements)
{
    return CreateArray (VNET_SHORT, pData + npFirstWriteElementIndex,
            sGetNumWriteElements (npMaxNumElements, npFirstWriteElementIndex, npNumWriteElements), sizeof (SHORT));
}

BOOL_P CVolComVariant::CreateArray_TCHAR (const TCHAR* pData, const INT_P npMaxNumElements, INT_P npFirstWriteElementIndex, INT_P npNumWriteElements)
{
    COMPILE_TIME_ASSERT (sizeof (SHORT) == sizeof (TCHAR));
    return CreateArray_SHORT ((const SHORT*)pData, npMaxNumElements, npFirstWriteElementIndex, npNumWriteElements);
}

BOOL_P CVolComVariant::CreateArray_INT (const INT* pData, const INT_P npMaxNumElements, INT_P npFirstWriteElementIndex, INT_P npNumWriteElements)
{
    return CreateArray (VNET_INT, pData + npFirstWriteElementIndex,
            sGetNumWriteElements (npMaxNumElements, npFirstWriteElementIndex, npNumWriteElements), sizeof (INT));
}

BOOL_P CVolComVariant::CreateArray_INT64 (const INT64* pData, const INT_P npMaxNumElements, INT_P npFirstWriteElementIndex, INT_P npNumWriteElements)
{
    return CreateArray (VNET_LONG, pData + npFirstWriteElementIndex,
            sGetNumWriteElements (npMaxNumElements, npFirstWriteElementIndex, npNumWriteElements), sizeof (INT64));
}

BOOL_P CVolComVariant::CreateArray_FLOAT (const FLOAT* pData, const INT_P npMaxNumElements, INT_P npFirstWriteElementIndex, INT_P npNumWriteElements)
{
    return CreateArray (VNET_FLOAT, pData + npFirstWriteElementIndex,
            sGetNumWriteElements (npMaxNumElements, npFirstWriteElementIndex, npNumWriteElements), sizeof (FLOAT));
}

BOOL_P CVolComVariant::CreateArray_DOUBLE (const DOUBLE* pData, const INT_P npMaxNumElements, INT_P npFirstWriteElementIndex, INT_P npNumWriteElements)
{
    return CreateArray (VNET_DOUBLE, pData + npFirstWriteElementIndex,
            sGetNumWriteElements (npMaxNumElements, npFirstWriteElementIndex, npNumWriteElements), sizeof (DOUBLE));
}

BOOL_P CVolComVariant::CreateArray_BOOL (const BOOL* pData, const INT_P npMaxNumElements, INT_P npFirstWriteElementIndex, INT_P npNumWriteElements)
{
    npNumWriteElements = sGetNumWriteElements (npMaxNumElements, npFirstWriteElementIndex, npNumWriteElements);
    ASSERT_R_ADR (pData + npFirstWriteElementIndex, npNumWriteElements * sizeof (BOOL));

    if (CreateEmptyArray (VNET_BOOL, npNumWriteElements) == FALSE)
        return FALSE;

    ASSERT (m_var.parray != NULL && npNumWriteElements >= 0 &&  // CreateEmptyArray中算法决定
            sGetSafeArrayElementCount (m_var.parray) == npNumWriteElements &&
            (INT_P)::SafeArrayGetElemsize (m_var.parray) == sizeof (VARIANT_BOOL));
    
    if (npNumWriteElements == 0)
        return TRUE;

    BYTE HUGEP *pb;
    if (SUCCEEDED (::SafeArrayAccessData (m_var.parray, (void HUGEP**)&pb)))
    {
        const BOOL* pblSource = pData + npFirstWriteElementIndex;
        VARIANT_BOOL* pblDest = (VARIANT_BOOL*)pb;

        for (INT_P npIndex = 0; npIndex < npNumWriteElements; npIndex++, pblSource++, pblDest++)
            *pblDest = (*pblSource ? -1 : 0);

        ::SafeArrayUnaccessData (m_var.parray);
        return TRUE;
    }

    return FALSE;
}

BOOL_P CVolComVariant::CreateArray_CVolString (const CVolString* pData, const INT_P npMaxNumElements, INT_P npFirstWriteElementIndex, INT_P npNumWriteElements)
{
    npNumWriteElements = sGetNumWriteElements (npMaxNumElements, npFirstWriteElementIndex, npNumWriteElements);
    ASSERT_R_ADR (pData + npFirstWriteElementIndex, npNumWriteElements * sizeof (CVolString));

    if (CreateEmptyArray (VNET_STR, npNumWriteElements) == FALSE)
        return FALSE;

    ASSERT (m_var.parray != NULL && npNumWriteElements >= 0 &&  // CreateEmptyArray中算法决定
            sGetSafeArrayElementCount (m_var.parray) == npNumWriteElements &&
            (INT_P)::SafeArrayGetElemsize (m_var.parray) == sizeof (BSTR));
    
    if (npNumWriteElements == 0)
        return TRUE;

    BYTE HUGEP *pb;
    if (SUCCEEDED (::SafeArrayAccessData (m_var.parray, (void HUGEP**)&pb)))
    {
        const CVolString* pstrSource = pData + npFirstWriteElementIndex;
        BSTR* pbstrDest = (BSTR*)pb;

        for (INT_P npIndex = 0; npIndex < npNumWriteElements; npIndex++, pstrSource++, pbstrDest++)
            *pbstrDest = ::SysAllocString (pstrSource->GetText ());

        ::SafeArrayUnaccessData (m_var.parray);
        return TRUE;
    }

    return FALSE;
}

BOOL_P CVolComVariant::CreateArray_Variant (const CVolComVariant* pData, const INT_P npMaxNumElements, INT_P npFirstWriteElementIndex, INT_P npNumWriteElements)
{
    npNumWriteElements = sGetNumWriteElements (npMaxNumElements, npFirstWriteElementIndex, npNumWriteElements);
    ASSERT_R_ADR (pData + npFirstWriteElementIndex, npNumWriteElements * sizeof (CVolComVariant));

    if (CreateEmptyArray (VNET_VARIANT, npNumWriteElements) == FALSE)
        return FALSE;

    ASSERT (m_var.parray != NULL && npNumWriteElements >= 0 &&  // CreateEmptyArray中算法决定
            sGetSafeArrayElementCount (m_var.parray) == npNumWriteElements &&
            (INT_P)::SafeArrayGetElemsize (m_var.parray) == sizeof (VARIANT));
    
    if (npNumWriteElements == 0)
        return TRUE;

    BYTE HUGEP *pb;
    if (SUCCEEDED (::SafeArrayAccessData (m_var.parray, (void HUGEP**)&pb)))
    {
        const CVolComVariant* pvSource = pData + npFirstWriteElementIndex;
        VARIANT* pvDest = (VARIANT*)pb;

        for (INT_P npIndex = 0; npIndex < npNumWriteElements; npIndex++, pvSource++, pvDest++)
            ::VariantCopyInd (pvDest, &pvSource->m_var);

        ::SafeArrayUnaccessData (m_var.parray);
        return TRUE;
    }

    return FALSE;
}

BOOL_P CVolComVariant::CreateArray_ComObject (const CVolComObject* pData, const INT_P npMaxNumElements, INT_P npFirstWriteElementIndex, INT_P npNumWriteElements)
{
    npNumWriteElements = sGetNumWriteElements (npMaxNumElements, npFirstWriteElementIndex, npNumWriteElements);
    ASSERT_R_ADR (pData + npFirstWriteElementIndex, npNumWriteElements * sizeof (CVolComObject));

    if (CreateEmptyArray (VNET_COM_OBJECT, npNumWriteElements) == FALSE)
        return FALSE;

    ASSERT (m_var.parray != NULL && npNumWriteElements >= 0 &&  // CreateEmptyArray中算法决定
            sGetSafeArrayElementCount (m_var.parray) == npNumWriteElements &&
            (INT_P)::SafeArrayGetElemsize (m_var.parray) == sizeof (IUnknown*));
    
    if (npNumWriteElements == 0)
        return TRUE;

    BYTE HUGEP *pb;
    if (SUCCEEDED (::SafeArrayAccessData (m_var.parray, (void HUGEP**)&pb)))
    {
        const CVolComObject* pobjSource = pData + npFirstWriteElementIndex;
        IUnknown** ppobjDest = (IUnknown**)pb;

        for (INT_P npIndex = 0; npIndex < npNumWriteElements; npIndex++, pobjSource++, ppobjDest++)
        {
            if (pobjSource->m_pUnknownObject != NULL)
                pobjSource->m_pUnknownObject->AddRef ();

            if (*ppobjDest != NULL)
                (*ppobjDest)->Release ();

            *ppobjDest = pobjSource->m_pUnknownObject;
        }

        ::SafeArrayUnaccessData (m_var.parray);
        return TRUE;
    }

    return FALSE;
}

BOOL_P CVolComVariant::CreateArray_ComDispatchObject (const CVolComObject* pData, const INT_P npMaxNumElements, INT_P npFirstWriteElementIndex, INT_P npNumWriteElements)
{
    npNumWriteElements = sGetNumWriteElements (npMaxNumElements, npFirstWriteElementIndex, npNumWriteElements);
    ASSERT_R_ADR (pData + npFirstWriteElementIndex, npNumWriteElements * sizeof (CVolComObject));

    if (CreateEmptyArray (VNET_COM_DISPATCH, npNumWriteElements) == FALSE)
        return FALSE;

    ASSERT (m_var.parray != NULL && npNumWriteElements >= 0 &&  // CreateEmptyArray中算法决定
            sGetSafeArrayElementCount (m_var.parray) == npNumWriteElements &&
            (INT_P)::SafeArrayGetElemsize (m_var.parray) == sizeof (IUnknown*));
    
    if (npNumWriteElements == 0)
        return TRUE;

    BYTE HUGEP *pb;
    if (SUCCEEDED (::SafeArrayAccessData (m_var.parray, (void HUGEP**)&pb)))
    {
        const CVolComObject* pobjSource = pData + npFirstWriteElementIndex;
        IDispatch** ppobjDest = (IDispatch**)pb;

        for (INT_P npIndex = 0; npIndex < npNumWriteElements; npIndex++, pobjSource++, ppobjDest++)
        {
            IDispatch* pDispatch;
            if (pobjSource->m_pUnknownObject != NULL &&
                    SUCCEEDED (pobjSource->m_pUnknownObject->QueryInterface (IID_IDispatch, (LPVOID*)&pDispatch)))
            {
                ASSERT (pDispatch != NULL);
            }
            else
                pDispatch = NULL;

            if (*ppobjDest != NULL)
                (*ppobjDest)->Release ();

            *ppobjDest = pDispatch;
        }

        ::SafeArrayUnaccessData (m_var.parray);
        return TRUE;
    }

    return FALSE;
}

void CVolComVariant::GetDumpString (CVolString& strDump, INT nMaxDumpSize)
{
    if (m_var.vt == VT_EMPTY)
    {
        strDump.AddText (_T_VARIANT_EMPTY);
        return;
    }

    const VARTYPE vtElement = (m_var.vt & VT_TYPEMASK);
    const BOOL_P blpIsRef = ((m_var.vt & VT_BYREF) != 0);  // 获得是否为参考数据
    const BOOL_P blpIsArray = ((m_var.vt & VT_ARRAY) != 0);  // 获得是否为数组数据

    strDump.AddText (_T ("{ "));

    #define _ADD_VARIANT_TYPE_STR(vartype)  case vartype:  strDump.AddText (_T (#vartype));  break;
    switch (vtElement)
    {
    _ADD_VARIANT_TYPE_STR (VT_I1)
    _ADD_VARIANT_TYPE_STR (VT_I2)
    _ADD_VARIANT_TYPE_STR (VT_I4)
    _ADD_VARIANT_TYPE_STR (VT_I8)
    _ADD_VARIANT_TYPE_STR (VT_UI1)
    _ADD_VARIANT_TYPE_STR (VT_UI2)
    _ADD_VARIANT_TYPE_STR (VT_UI4)
    _ADD_VARIANT_TYPE_STR (VT_UI8)
    _ADD_VARIANT_TYPE_STR (VT_INT)
    _ADD_VARIANT_TYPE_STR (VT_UINT)
    _ADD_VARIANT_TYPE_STR (VT_R4)
    _ADD_VARIANT_TYPE_STR (VT_R8)
    _ADD_VARIANT_TYPE_STR (VT_BOOL)
    _ADD_VARIANT_TYPE_STR (VT_CY)
    _ADD_VARIANT_TYPE_STR (VT_DATE)
    _ADD_VARIANT_TYPE_STR (VT_DECIMAL)
    _ADD_VARIANT_TYPE_STR (VT_ERROR)
    _ADD_VARIANT_TYPE_STR (VT_VARIANT)
    _ADD_VARIANT_TYPE_STR (VT_BSTR)
    _ADD_VARIANT_TYPE_STR (VT_UNKNOWN)
    _ADD_VARIANT_TYPE_STR (VT_DISPATCH)
    default:  strDump.AddText (_T_VARIANT_UNKNOWN_TYPE);  return;
    }

    if (blpIsRef)
        strDump.AddText (_T_VARIANT_REF);
    if (blpIsArray)
        strDump.AddText (_T_VARIANT_ARRAY);

    if (blpIsRef == FALSE && blpIsArray == FALSE)
    {
        strDump.AddText (_T (": "));

        switch (vtElement)
        {
        case VT_I1:  strDump.AddIntText (m_var.cVal);  break;
        case VT_I2:  strDump.AddIntText (m_var.iVal);  break;
        case VT_I4:  strDump.AddIntText (m_var.lVal);  break;
        case VT_I8:  strDump.AddInt64Text (m_var.llVal);  break;
        case VT_UI1:  strDump.AddIntText ((INT)(DWORD)m_var.bVal);  break;
        case VT_UI2:  strDump.AddIntText ((INT)(DWORD)m_var.uiVal);  break;
        case VT_UI4:  strDump.AddIntText ((INT)m_var.ulVal);  break;
        case VT_UI8:  strDump.AddInt64Text ((INT64)m_var.ullVal);  break;
        case VT_INT:  strDump.AddIntText (m_var.intVal);  break;
        case VT_UINT:  strDump.AddIntText ((INT)m_var.uintVal);  break;
        case VT_R4:  strDump.AddFloatText (m_var.fltVal);  break;
        case VT_R8:  strDump.AddDoubleText (m_var.dblVal);  break;
        case VT_BOOL:  strDump.AddText (m_var.boolVal != 0 ? _T_V_TRUE : _T_V_FALSE);  break;
        case VT_BSTR:
            if (m_var.bstrVal == NULL)
                strDump.AddText (_T_VARIANT_NULL_STR_POINTER);
            else
            {
                CVolString strBuf;
                strDump.AddText (MakeStringFromPlainText (m_var.bstrVal, &strBuf, TRUE));
            }
            break;
        default:  strDump.AddText (_T_VARIANT_UNKNOWN_VALUE);  break;
        }
    }

    strDump.AddText (_T (" }"));
}

//------------------------------------------------------------------------------------------------

void CVolComObject::GetDumpString (CVolString& strDump, INT nMaxDumpSize)
{
    if (m_pUnknownObject == NULL)
        strDump.AddText (_T_VARIANT_EMPTY);
    else
        strDump.AddFormatText (_T (" { IUnknown*: 0x") _TF_HP _T (" }"), (UINT_P)m_pUnknownObject);
}

void CVolComObject::_CopySelfFrom (const CVolComObject& objCopyFrom)
{
    SetUnknownObject (objCopyFrom.m_pUnknownObject);
}

BOOL CVolComObject::_IsSelfEqual (const CVolComObject& objCompare) const
{
    if (m_pUnknownObject == NULL || objCompare.m_pUnknownObject == NULL)
        return (m_pUnknownObject == objCompare.m_pUnknownObject);

    IUnknown* pCompareUnk1 = NULL;
    IUnknown* pCompareUnk2 = NULL;

    // 查询IUnknown接口指针以进行对比
    BOOL_P blpEqual;
    if (FAILED (m_pUnknownObject->QueryInterface (IID_IUnknown, (void**)&pCompareUnk1)) ||
            FAILED (objCompare.m_pUnknownObject->QueryInterface (IID_IUnknown, (void**)&pCompareUnk2)))
    {
        blpEqual = FALSE;
    }
    else
        blpEqual = (pCompareUnk1 == pCompareUnk2);

    if (pCompareUnk1 != NULL)
        pCompareUnk1->Release ();
    if (pCompareUnk2 != NULL)
        pCompareUnk2->Release ();

    return (BOOL)blpEqual;
}

void CVolComObject::ReleaseUnknownObject ()
{
    MSAFE_RELEASE (m_pUnknownObject)
    m_enInvokeResult = IRT_SUCCEEDED;
}

void CVolComObject::SetUnknownObject (IUnknown* pUnknownObject)
{
    ASSERT_R_DATA_OR_NULL (pUnknownObject);

    if (pUnknownObject != NULL)
        pUnknownObject->AddRef ();

    if (m_pUnknownObject != NULL)
        m_pUnknownObject->Release ();

    m_pUnknownObject = pUnknownObject;
}

void CVolComObject::TakeOverNewUnknownObject (IUnknown* pNewUnknownObject)
{
    if (m_pUnknownObject != NULL)
        m_pUnknownObject->Release ();

    m_pUnknownObject = pNewUnknownObject;
}

BOOL_P CVolComObject::sGetClassIDFromString (const TCHAR* szObjectTypeName, CLSID* pClsID)
{
    ASSERT (szObjectTypeName != NULL && pClsID != NULL);

    if (IsEmptyStr (szObjectTypeName))
        return FALSE;

    return SUCCEEDED (szObjectTypeName [0] == '{' ?
            CLSIDFromString ((LPCOLESTR)szObjectTypeName, pClsID) : CLSIDFromProgID ((LPCOLESTR)szObjectTypeName, pClsID));
}

BOOL_P CVolComObject::CreateComObject (const TCHAR* szObjectTypeName, const TCHAR* szTypeLibFileName)
{
    IUnknown* pUnknownObject = NULL;
    szObjectTypeName = SkipSpaces (szObjectTypeName);

    if (*szObjectTypeName != '{' && IsEmptyStr (szTypeLibFileName) == FALSE)
    {
        ITypeLib* pTypeLib;

        if (SUCCEEDED (LoadTypeLib (szTypeLibFileName, &pTypeLib)))
        {
            ITypeInfo* pTypeInfo;
            MEMBERID id;
            WORD cFound = 1;

            if (SUCCEEDED (pTypeLib->FindName ((TCHAR*)szObjectTypeName,
                    LHashValOfNameSys (SYS_WIN32, GetUserDefaultLCID (), szObjectTypeName),
                    &pTypeInfo, &id, &cFound)) && cFound == 1)
            {
                if (FAILED (pTypeInfo->CreateInstance (NULL, IID_IUnknown, (void**)&pUnknownObject)))
                {
                    pUnknownObject = NULL;
                }
                else if (_tcschr (szTypeLibFileName, '\\') != NULL)  // 文件名包含路径?
                {
                    // 登记它以便后面能够正常取出对象的类型信息(无路径的类型库会被LoadTypeLib自动登记)
                    RegisterTypeLib (pTypeLib, szTypeLibFileName, NULL);
                }

                pTypeInfo->Release ();
            }

            pTypeLib->Release ();
        }
    }

    if (pUnknownObject == NULL)
    {
        CLSID clsid;
        if (sGetClassIDFromString (szObjectTypeName, &clsid) == FALSE)
            return FALSE;

        SCODE sc = CoCreateInstance (clsid, NULL, (CLSCTX_ALL | CLSCTX_REMOTE_SERVER), IID_IUnknown, (void**)&pUnknownObject);
        if (sc == E_INVALIDARG)
            sc = CoCreateInstance (clsid, NULL, (CLSCTX_ALL & ~CLSCTX_REMOTE_SERVER), IID_IUnknown, (void**)&pUnknownObject);

        if (FAILED (sc))
            return FALSE;
    }

    if (FAILED (OleRun (pUnknownObject)))
    {
        pUnknownObject->Release ();
        return FALSE;
    }

    TakeOverNewUnknownObject (pUnknownObject);
    return TRUE;
}

BOOL_P CVolComObject::QueryComObject (const TCHAR* szObjectTypeName)
{
    ASSERT_R_STR (szObjectTypeName);

    CLSID clsid;
    if (sGetClassIDFromString (szObjectTypeName, &clsid) == FALSE)
        return FALSE;

    IUnknown* pUnknownObject = NULL;
    if (FAILED (::GetActiveObject (clsid, NULL, &pUnknownObject)))
        return FALSE;

    TakeOverNewUnknownObject (pUnknownObject);
    return TRUE;
}

BOOL_P CVolComObject::QueryComInterface (const TCHAR* szInterfaceName, CVolComObject& objResult)
{
    ASSERT_R_STR (szInterfaceName);

    if (m_pUnknownObject == NULL)
        return FALSE;

    IID iid = IID_IUnknown;
    if (IsEmptyStr (szInterfaceName) == FALSE)
    {
        if (sGetClassIDFromString (szInterfaceName, &iid) == FALSE)
            return FALSE;
    }

    IUnknown* pUnknownObject;
    if (FAILED (m_pUnknownObject->QueryInterface (iid, (void**)&pUnknownObject)))
        return FALSE;

    objResult.TakeOverNewUnknownObject (pUnknownObject);
    return TRUE;
}

CVolComObject& CVolComObject::QueryComInterface2 (const TCHAR* szInterfaceName, CVolComObject& objResult)
{
    ASSERT_R_STR (szInterfaceName);

    objResult.ReleaseUnknownObject ();

    do
    {
        if (m_pUnknownObject == NULL)
            break;

        IID iid = IID_IUnknown;
        if (IsEmptyStr (szInterfaceName) == FALSE)
        {
            if (sGetClassIDFromString (szInterfaceName, &iid) == FALSE)
                break;
        }

        IUnknown* pUnknownObject;
        if (FAILED (m_pUnknownObject->QueryInterface (iid, (void**)&pUnknownObject)))
            break;

        objResult.TakeOverNewUnknownObject (pUnknownObject);
    }
    while (FALSE);

    return objResult;
}

BOOL_P CVolComObject::CreatePicDispObject (const HBITMAP hBitmap)
{
    if (hBitmap == NULL)
        return FALSE;

    const HBITMAP hCloneBitmap = (HBITMAP)::CopyImage (hBitmap, IMAGE_BITMAP, 0, 0, 0);
    if (hCloneBitmap == NULL)
        return FALSE;

    PICTDESC desc;
    ZERO_MEM (&desc, sizeof (desc));
    desc.cbSizeofstruct = sizeof (desc);
    desc.picType = PICTYPE_BITMAP;
    desc.bmp.hbitmap = hCloneBitmap;

    IPictureDisp* pPictureDisp;
    if (FAILED (OleCreatePictureIndirect (&desc, IID_IPictureDisp, TRUE, (void**)&pPictureDisp)))
    {
        ::DeleteObject (hCloneBitmap);
        return FALSE;
    }

    TakeOverNewUnknownObject (pPictureDisp);

    /* IUnknown* pUnknownObject;
    if (FAILED (pPictureDisp->QueryInterface (IID_IUnknown, (void**)&pUnknownObject)))
    {
        pPictureDisp->Release ();
        return FALSE;
    }

    pPictureDisp->Release ();

    TakeOverNewUnknownObject (pUnknownObject); */
    return TRUE;
}

BOOL_P CVolComObject::GetPicDispData (CVolMem& memResult)
{
    IPicture* pPicture = NULL;
    IStream* pStream = NULL;
    BOOL_P blpSucceeded = FALSE;

    do
    {
        if (m_pUnknownObject == NULL)
            break;

        if (FAILED (m_pUnknownObject->QueryInterface (IID_IPicture, (void**)&pPicture)) ||
                FAILED (CreateStreamOnHGlobal (NULL, TRUE, &pStream)))
        {
            break;
        }

        LONG lSize = 0;
        if (FAILED (pPicture->SaveAsFile (pStream, TRUE, &lSize)) || lSize <= 0)
            break;

        LARGE_INTEGER nDisplacement;
        nDisplacement.QuadPart = 0;
        pStream->Seek (nDisplacement, STREAM_SEEK_SET, NULL);

        ULONG ulRead;
        if (SUCCEEDED (pStream->Read (memResult.Alloc ((INT)lSize), (ULONG)lSize, &ulRead)) &&
                ulRead == (ULONG)lSize)
        {
            blpSucceeded = TRUE;
        }
        else
            memResult.Free ();
    }
    while (FALSE);

    if (pStream != NULL)
        pStream->Release ();

    if (pPicture != NULL)
        pPicture->Release ();

    return blpSucceeded;
}

void CVolComObject::sDoubleToCurrency (const DOUBLE db, CY* pcy)
{
    VARIANT var;
    VariantInit (&var);
    var.vt = VT_R8;
    var.dblVal = db;

    ::VariantChangeType (&var, &var, 0, VT_CY);
    *pcy = var.cyVal;

    VariantClear (&var);
}

DOUBLE CVolComObject::sCurrencyToDouble (const CY& cy)
{
    VARIANT var;
    VariantInit (&var);
    var.vt = VT_CY;
    var.cyVal = cy;

    VariantChangeType (&var, &var, 0, VT_R8);
    const DOUBLE db = var.dblVal;

    VariantClear (&var);
    return db;
}

BOOL_P CVolComObject::CreateFontDispObject (const HFONT hFont)
{
    if (hFont == NULL)
        return FALSE;

    LOGFONT infFont;
    ::GetObject (hFont, sizeof (LOGFONT), &infFont);

    return CreateFontDispObjectFromInfo (&infFont);
}

BOOL_P CVolComObject::CreateFontDispObjectFromInfo (const LOGFONT* pinfFont)
{
    ASSERT (pinfFont != NULL);

    FONTDESC desc;
    ZERO_MEM (&desc, sizeof (desc));

    desc.cbSizeofstruct = sizeof (desc);
    desc.lpstrName = (LPOLESTR)pinfFont->lfFaceName;
    sDoubleToCurrency (DoubleFontDpSize2Pt ((DOUBLE)pinfFont->lfHeight), &desc.cySize);
    desc.sWeight = (SHORT)pinfFont->lfWeight;
    desc.sCharset = (SHORT)pinfFont->lfCharSet;
    desc.fItalic = (BOOL)pinfFont->lfItalic;
    desc.fUnderline = (BOOL)pinfFont->lfUnderline;
    desc.fStrikethrough = (BOOL)pinfFont->lfStrikeOut;

    IFontDisp* pFontDisp;
    if (FAILED (OleCreateFontIndirect (&desc, IID_IFontDisp, (void**)&pFontDisp)))
        return FALSE;

    TakeOverNewUnknownObject (pFontDisp);

    /* IUnknown* pUnknownObject;
    if (FAILED (pFontDisp->QueryInterface (IID_IUnknown, (void**)&pUnknownObject)))
    {
        pFontDisp->Release ();
        return FALSE;
    }

    pFontDisp->Release ();

    TakeOverNewUnknownObject (pUnknownObject); */
    return TRUE;
}

HFONT CVolComObject::CreateFontFromDispData ()
{
    IFont* pFont = NULL;
    HFONT hResultFont = NULL;

    do
    {
        if (m_pUnknownObject == NULL)
            break;

        HFONT hFont;
        CY size;
        if (FAILED (m_pUnknownObject->QueryInterface (IID_IFont, (void**)&pFont)) ||
                FAILED (pFont->get_hFont (&hFont)) || FAILED (pFont->get_Size (&size)))
        {
            break;
        }

        LOGFONT infFont;
        if (::GetObject (hFont, sizeof (LOGFONT), &infFont) != 0)
        {
            infFont.lfHeight = -(INT)(fabs (DoubleFontPtSize2Dp (sCurrencyToDouble (size))) + 0.5);
            hResultFont = CreateFontIndirect (&infFont);
        }
    }
    while (FALSE);

    if (pFont != NULL)
        pFont->Release ();

    return hResultFont;
}

VARTYPE CVolComObject::sGetVarType (ITypeInfo* pTypeInfo, TYPEDESC* pTypeDesc)
{
    VARTYPE vt = (pTypeDesc->vt & VT_TYPEMASK);
    const VARTYPE vtByRef = (vt & VT_BYREF);
    const VARTYPE vtArray = (vt & VT_ARRAY);

    if (vt == VT_PTR)
        return (sGetVarType (pTypeInfo, pTypeDesc->lptdesc) | VT_BYREF | vtArray);

    if (vt == VT_SAFEARRAY)
        return (sGetVarType (pTypeInfo, pTypeDesc->lptdesc) | VT_ARRAY | vtByRef);

    if (vt == VT_CARRAY)
        return (sGetVarType (pTypeInfo, &pTypeDesc->lpadesc->tdescElem) | VT_ARRAY | vtByRef);

    if (vt == VT_INT)
        vt = VT_I4;
    else if (vt == VT_UINT)
        vt = VT_UI4;

    if (vt == VT_USERDEFINED)
    {
        vt = VT_UNKNOWN;

        ITypeInfo* ptiRefType = NULL;
        if (SUCCEEDED (pTypeInfo->GetRefTypeInfo (pTypeDesc->hreftype, &ptiRefType)))
        {
            TYPEATTR* pattr = NULL;

            if (SUCCEEDED (ptiRefType->GetTypeAttr (&pattr)))
            {
                switch (pattr->typekind)
                {
                case TKIND_ALIAS:
                    vt = sGetVarType (ptiRefType, &pattr->tdescAlias);
                    break;

                case TKIND_ENUM:
                    vt = VT_I4;
                    break;

                case TKIND_DISPATCH:
                    vt = VT_DISPATCH;
                    break;
                }

                ptiRefType->ReleaseTypeAttr (pattr);
            }

            ptiRefType->Release ();
        }
    }

    return (vt | vtByRef | vtArray);
}

BOOL CVolComObject::sMakeRefVaiant (VARIANT* pDest, VARIANT* pSrc)
{
    ASSERT (pDest != NULL && pSrc != NULL);

    switch (pSrc->vt)
    {
    case VT_I1:  pDest->pcVal = &pSrc->cVal;  break;
    case VT_I2:  pDest->piVal = &pSrc->iVal;  break;
    case VT_I4:  pDest->plVal = &pSrc->lVal;  break;
    case VT_I8:  pDest->pllVal = &pSrc->llVal;  break;
    case VT_UI1:  pDest->pbVal = &pSrc->bVal;  break;
    case VT_UI2:  pDest->puiVal = &pSrc->uiVal;  break;
    case VT_UI4:  pDest->pulVal = &pSrc->ulVal;  break;
    case VT_UI8:  pDest->pullVal = &pSrc->ullVal;  break;
    case VT_INT:  pDest->pintVal = &pSrc->intVal;  break;
    case VT_UINT:  pDest->puintVal = &pSrc->uintVal;  break;
    case VT_HRESULT:
    case VT_ERROR:  pDest->pscode = &pSrc->scode;  break;
    case VT_R4:  pDest->pfltVal = &pSrc->fltVal;  break;
    case VT_R8:  pDest->pdblVal = &pSrc->dblVal;  break;
    case VT_CY:  pDest->pcyVal = &pSrc->cyVal;  break;
    case VT_DATE:  pDest->pdate = &pSrc->date;  break;
    case VT_BSTR:  pDest->pbstrVal = &pSrc->bstrVal;  break;
    case VT_BOOL:  pDest->pboolVal = &pSrc->boolVal;  break;
    case VT_VARIANT:  pDest->pvarVal = pSrc;  break;
    case VT_UNKNOWN:  pDest->ppunkVal = &pSrc->punkVal;  break;
    case VT_DISPATCH:  pDest->ppdispVal = &pSrc->pdispVal;  break;
    default:  return FALSE;
    }

    pDest->vt = (pSrc->vt | VT_BYREF);
    return TRUE;
}

INT_P CVolComObject::sParseCallParams (va_list argList, const INT_P npFirstExtendParamTypeIndex,
        const TCHAR* szParamTypes, INVOKE_CALL_PARAM_DATA** ppCallParamDataBegin, CVolMem& memResult)
{
    ASSERT (szParamTypes != NULL && ppCallParamDataBegin != NULL);

    *ppCallParamDataBegin = NULL;
    const CVolUserApp& objVolUserApp = g_objVolApp.GetVolApp ();

    const INT_P npNumParams = _tcslen (szParamTypes);
    ASSERT (npNumParams >= npFirstExtendParamTypeIndex);

    INVOKE_CALL_PARAM_DATA* pinfData = (INVOKE_CALL_PARAM_DATA*)memResult.Alloc (
            sizeof (INVOKE_CALL_PARAM_DATA) * (npNumParams - npFirstExtendParamTypeIndex));
    memResult.Zero ();

    for (INT_P npParamIndex = npFirstExtendParamTypeIndex; npParamIndex < npNumParams; npParamIndex++, pinfData++)
    {
        switch (szParamTypes [npParamIndex])
        {
        case _C_VOL_SBYTE:  // 字节
            pinfData->m_enType = ICPT_SBYTE;
            pinfData->m_sbyte = va_arg (argList, S_BYTE);
            break;

        case _C_VOL_SHORT:  // 短整数
            pinfData->m_enType = ICPT_SHORT;
            pinfData->m_short = va_arg (argList, SHORT);
            break;

        case _C_VOL_WCHAR:  // 字符
            pinfData->m_enType = ICPT_WCHAR;
            pinfData->m_char = va_arg (argList, TCHAR);
            break;

        case _C_VOL_INT:  // 整数
            pinfData->m_enType = ICPT_INT;
            pinfData->m_int = va_arg (argList, INT);
            break;

        case _C_VOL_VINT:  // 变整数
        case _C_VOL_METHOD:  // 方法名
        case _C_NATIVE_REF_DATA_TYPE:  // 本地参考类型
            pinfData->m_enType = ICPT_VINT;
            pinfData->m_vint = va_arg (argList, INT_P);
            break;

        case _C_VOL_LONG:  // 长整数
            pinfData->m_enType = ICPT_LONG;
            pinfData->m_long = va_arg (argList, INT64);
            break;

        case _C_VOL_FLOAT:  // 单精度小数
            pinfData->m_enType = ICPT_FLOAT;
            pinfData->m_float = (FLOAT)va_arg (argList, DOUBLE);  // FLOAT在VC中是使用DOUBLE方式传递的
            break;

        case _C_VOL_DOUBLE:  // 小数
            pinfData->m_enType = ICPT_DOUBLE;
            pinfData->m_double = va_arg (argList, DOUBLE);
            break;

        case _C_VOL_BOOL:  // 逻辑型
            pinfData->m_enType = ICPT_BOOL;
            pinfData->m_bool = va_arg (argList, BOOL);
            break;

        case _C_VOL_STRING:  // 文本型
            pinfData->m_enType = ICPT_P_STRING;  // 调用InvokeComMethodV的火山嵌入式方法的属性表中必须定义了"req_obj_param_pointer"属性
            pinfData->m_pStr = va_arg (argList, CVolString*);
            ASSERT (pinfData->m_pStr != NULL);
            break;

        case _C_VOL_CLASS:  {  // 火山类
            // 调用InvokeComMethodV的火山嵌入式方法的属性表中必须定义了"req_obj_param_pointer"属性
            CVolObject* pVolObject = va_arg (argList, CVolObject*);
            ASSERT (pVolObject != NULL);

            if (pVolObject->IsNullObject ())  // 为空对象?
            {
                pinfData->m_enType = ICPT_EMPTY;
            }
            else if (P_IS_VOL_INSTANCE_OF (pVolObject, CVolComVariant))
            {
                pinfData->m_enType = ICPT_P_COM_VARIANT;
                pinfData->m_pVolComVariant = (CVolComVariant*)pVolObject;
            }
            else if (P_IS_VOL_INSTANCE_OF (pVolObject, CVolComObject))
            {
                pinfData->m_enType = ICPT_P_COM_OBJECT;
                pinfData->m_pVolComObject = (CVolComObject*)pVolObject;
            }
            else if (P_IS_VOL_INSTANCE_OF (pVolObject, CVolBaseDataType))
            {
                const void* pData = ((CVolBaseDataType*)pVolObject)->GetDataPtr ();
                const CVolUserApp::SPEC_USER_CLASS_TYPE enSpecUserClassType = objVolUserApp.FindSpecialUserClassType (pVolObject);

                switch (enSpecUserClassType)
                {
                case CVolUserApp::SUCT_PKG_SBYTE:  // 字节类
                    pinfData->m_enType = ICPT_P_SBYTE;
                    pinfData->m_pSByte = (S_BYTE*)pData;
                    break;

                case CVolUserApp::SUCT_PKG_SHORT:  // 短整数类
                    pinfData->m_enType = ICPT_P_SHORT;
                    pinfData->m_pShort = (SHORT*)pData;
                    break;

                case CVolUserApp::SUCT_PKG_WCHAR:  // 字符类
                    pinfData->m_enType = ICPT_P_WCHAR;
                    pinfData->m_pChar = (TCHAR*)pData;
                    break;

                case CVolUserApp::SUCT_PKG_INT:  // 整数类
                    pinfData->m_enType = ICPT_P_INT;
                    pinfData->m_pInt = (INT*)pData;
                    break;

                case CVolUserApp::SUCT_PKG_VINT:  // 变整数类
                    pinfData->m_enType = ICPT_P_VINT;
                    pinfData->m_pVInt = (INT_P*)pData;
                    break;

                case CVolUserApp::SUCT_PKG_LONG:  // 长整数类
                    pinfData->m_enType = ICPT_P_LONG;
                    pinfData->m_pLong = (INT64*)pData;
                    break;

                case CVolUserApp::SUCT_PKG_FLOAT:  // 单精度小数类
                    pinfData->m_enType = ICPT_P_FLOAT;
                    pinfData->m_pFloat = (FLOAT*)pData;
                    break;

                case CVolUserApp::SUCT_PKG_DOUBLE:  // 小数类
                    pinfData->m_enType = ICPT_P_DOUBLE;
                    pinfData->m_pDouble = (DOUBLE*)pData;
                    break;

                case CVolUserApp::SUCT_PKG_BOOL:  // 逻辑型类
                    pinfData->m_enType = ICPT_P_BOOL;
                    pinfData->m_pBool = (BOOL*)pData;
                    break;

                default:
                    FAIL;  // 正常情况下不会如此
                    return -1;
                }
            }
            else
            {
                return -1;
            }
            break;  }

        default:
            return -1;
        }
    }
    ASSERT (memResult.IsAtEnd (pinfData));

    *ppCallParamDataBegin = (INVOKE_CALL_PARAM_DATA*)memResult.GetPtr ();
    return npNumParams - npFirstExtendParamTypeIndex;
}

BOOL_P CVolComObject::sFillRefParamResult (INVOKE_CALL_PARAM_DATA* pCallParamData, const VARIANTARG* pParamVar)
{
    ASSERT (pCallParamData != NULL && pParamVar != NULL &&
            IS_POINTER_CALL_PARAM (pCallParamData->m_enType));  // 进入本方法的前提

    if (pCallParamData->m_enType == ICPT_P_COM_VARIANT)
    {
        VariantCopyInd (&pCallParamData->m_pVolComVariant->m_var, pParamVar);
        return TRUE;
    }

    VARIANTARG var;
    VariantInit (&var);

    BOOL_P blpSucceeded = TRUE;

    do
    {
        if (FAILED (VariantCopyInd (&var, pParamVar)))
        {
            blpSucceeded = FALSE;
            break;
        }

        VARTYPE vt;
        switch (pCallParamData->m_enType)
        {
        case ICPT_P_SBYTE:  vt = VT_I1;  break;
        case ICPT_P_SHORT:  vt = VT_I2;  break;
        case ICPT_P_WCHAR:  vt = VT_UI2;  break;
        case ICPT_P_INT:  vt = VT_I4;  break;
    #ifndef _PF_64_BITS
        case ICPT_P_VINT:  vt = VT_I4;  break;
    #else
        case ICPT_P_VINT:  vt = VT_I8;  break;
    #endif
        case ICPT_P_LONG:  vt = VT_I8;  break;
        case ICPT_P_FLOAT:  vt = VT_R4;  break;
        case ICPT_P_DOUBLE:  vt = VT_R8;  break;
        case ICPT_P_BOOL:  vt = VT_BOOL;  break;
        case ICPT_P_STRING:  vt = VT_BSTR;  break;
        case ICPT_P_COM_OBJECT:  vt = VT_UNKNOWN;  break;
        default:  blpSucceeded = FALSE;  break;
        }

        if (blpSucceeded == FALSE)
            break;

        if (FAILED (VariantChangeType (&var, &var, 0, vt)))
        {
            blpSucceeded = FALSE;
            break;
        }

        switch (pCallParamData->m_enType)
        {
        case ICPT_P_SBYTE:  *pCallParamData->m_pSByte = var.cVal;  break;
        case ICPT_P_SHORT:  *pCallParamData->m_pShort = var.iVal;  break;
        case ICPT_P_WCHAR:  *pCallParamData->m_pChar = (TCHAR)var.uiVal;  break;
        case ICPT_P_INT:  *pCallParamData->m_pInt = var.lVal;  break;
    #ifndef _PF_64_BITS
        case ICPT_P_VINT:  *pCallParamData->m_pVInt = var.lVal;  break;
    #else
        case ICPT_P_VINT:  *pCallParamData->m_pVInt = var.llVal;  break;
    #endif
        case ICPT_P_LONG:  *pCallParamData->m_pLong = var.llVal;  break;
        case ICPT_P_FLOAT:  *pCallParamData->m_pFloat = var.fltVal;  break;
        case ICPT_P_DOUBLE:  *pCallParamData->m_pDouble = var.dblVal;  break;
        case ICPT_P_BOOL:  *pCallParamData->m_pBool = (var.boolVal != 0);  break;
        case ICPT_P_STRING:  pCallParamData->m_pStr->SetText (var.bstrVal);  break;
        case ICPT_P_COM_OBJECT:  pCallParamData->m_pVolComObject->SetUnknownObject (var.punkVal);  break;
        DEFAULT_FAIL
        }
    }
    while (FALSE);

    VariantClear (&var);
    return blpSucceeded;
}

/* BOOL_P CVolComObject::ParseCallResult (const TCHAR chResultParamType, void* pResult, VARIANT* pvInvokeResult)
{
    ASSERT (chResultParamType != '\0' && pResult != NULL && pvInvokeResult != NULL);

    switch (chResultParamType)
    {
    case _C_VOL_SBYTE:
        if (SUCCEEDED (::VariantChangeType (pvInvokeResult, pvInvokeResult, 0, VT_I1)))
        {
            *(S_BYTE*)pResult = (S_BYTE)pvInvokeResult->cVal;
            return TRUE;
        }
        break;

    case _C_VOL_SHORT:
        if (SUCCEEDED (::VariantChangeType (pvInvokeResult, pvInvokeResult, 0, VT_I2)))
        {
            *(SHORT*)pResult = pvInvokeResult->iVal;
            return TRUE;
        }
        break;

    case _C_VOL_WCHAR:
        if (SUCCEEDED (::VariantChangeType (pvInvokeResult, pvInvokeResult, 0, VT_UI2)))
        {
            *(TCHAR*)pResult = (TCHAR)pvInvokeResult->uiVal;
            return TRUE;
        }
        break;

    case _C_VOL_INT:
#ifndef _PF_64_BITS
    case _C_VOL_VINT:
#endif
        if (SUCCEEDED (::VariantChangeType (pvInvokeResult, pvInvokeResult, 0, VT_I4)))
        {
            *(INT*)pResult = (INT)pvInvokeResult->lVal;
            return TRUE;
        }
        break;

    case _C_VOL_LONG:
#ifdef _PF_64_BITS
    case _C_VOL_VINT:
#endif
        if (SUCCEEDED (::VariantChangeType (pvInvokeResult, pvInvokeResult, 0, VT_I8)))
        {
            *(INT64*)pResult = (INT64)pvInvokeResult->llVal;
            return TRUE;
        }
        break;

    case _C_VOL_FLOAT:
        if (SUCCEEDED (::VariantChangeType (pvInvokeResult, pvInvokeResult, 0, VT_R4)))
        {
            *(FLOAT*)pResult = pvInvokeResult->fltVal;
            return TRUE;
        }
        break;

    case _C_VOL_DOUBLE:
        if (SUCCEEDED (::VariantChangeType (pvInvokeResult, pvInvokeResult, 0, VT_R8)))
        {
            *(DOUBLE*)pResult = pvInvokeResult->dblVal;
            return TRUE;
        }
        break;

    case _C_VOL_BOOL:
        if (SUCCEEDED (::VariantChangeType (pvInvokeResult, pvInvokeResult, 0, VT_BOOL)))
        {
            *(BOOL*)pResult = (pvInvokeResult->boolVal != 0);
            return TRUE;
        }
        break;

    case _C_VOL_STRING:
        if (SUCCEEDED (::VariantChangeType (pvInvokeResult, pvInvokeResult, 0, VT_BSTR)))
        {
            ((CVolString*)pResult)->SetText (pvInvokeResult->bstrVal);
            return TRUE;
        }
        break;

    case _C_VOL_CLASS:  {
        CVolObject* pVolObject = (CVolObject*)pResult;

        if (P_IS_VOL_INSTANCE_OF (pVolObject, CVolComVariant))
        {
            ::VariantCopyInd (&((CVolComVariant*)pVolObject)->m_var, pvInvokeResult);
            return TRUE;
        }
        else if (P_IS_VOL_INSTANCE_OF (pVolObject, CVolComObject))
        {
            if (SUCCEEDED (::VariantChangeType (pvInvokeResult, pvInvokeResult, 0, VT_UNKNOWN)))
            {
                ((CVolComObject*)pVolObject)->SetUnknownObject (pvInvokeResult->punkVal);
                return TRUE;
            }
        }
        else if (P_IS_VOL_INSTANCE_OF (pVolObject, CVolBaseDataType))
        {
            const void* pData = ((CVolBaseDataType*)pVolObject)->GetDataPtr ();
            const CVolUserApp::SPEC_USER_CLASS_TYPE enSpecUserClassType = g_objVolApp.GetVolApp ().FindSpecialUserClassType (pVolObject);

            switch (enSpecUserClassType)
            {
            case CVolUserApp::SUCT_PKG_SBYTE:  // 字节类
                if (SUCCEEDED (::VariantChangeType (pvInvokeResult, pvInvokeResult, 0, VT_I1)))
                {
                    *(S_BYTE*)pData = (S_BYTE)pvInvokeResult->cVal;
                    return TRUE;
                }
                break;

            case CVolUserApp::SUCT_PKG_SHORT:  // 短整数类
                if (SUCCEEDED (::VariantChangeType (pvInvokeResult, pvInvokeResult, 0, VT_I2)))
                {
                    *(SHORT*)pData = pvInvokeResult->iVal;
                    return TRUE;
                }
                break;

            case CVolUserApp::SUCT_PKG_WCHAR:  // 字符类
                if (SUCCEEDED (::VariantChangeType (pvInvokeResult, pvInvokeResult, 0, VT_UI2)))
                {
                    *(TCHAR*)pData = (TCHAR)pvInvokeResult->uiVal;
                    return TRUE;
                }
                break;

            case CVolUserApp::SUCT_PKG_INT:  // 整数类
        #ifndef _PF_64_BITS
            case CVolUserApp::SUCT_PKG_VINT:  // 变整数类
        #endif
                if (SUCCEEDED (::VariantChangeType (pvInvokeResult, pvInvokeResult, 0, VT_I4)))
                {
                    *(INT*)pData = (INT)pvInvokeResult->lVal;
                    return TRUE;
                }
                break;

            case CVolUserApp::SUCT_PKG_LONG:  // 长整数类
        #ifdef _PF_64_BITS
            case CVolUserApp::SUCT_PKG_VINT:  // 变整数类
        #endif
                if (SUCCEEDED (::VariantChangeType (pvInvokeResult, pvInvokeResult, 0, VT_I8)))
                {
                    *(INT64*)pData = (INT64)pvInvokeResult->llVal;
                    return TRUE;
                }
                break;

            case CVolUserApp::SUCT_PKG_FLOAT:  // 单精度小数类
                if (SUCCEEDED (::VariantChangeType (pvInvokeResult, pvInvokeResult, 0, VT_R4)))
                {
                    *(FLOAT*)pData = pvInvokeResult->fltVal;
                    return TRUE;
                }
                break;

            case CVolUserApp::SUCT_PKG_DOUBLE:  // 小数类
                if (SUCCEEDED (::VariantChangeType (pvInvokeResult, pvInvokeResult, 0, VT_R8)))
                {
                    *(DOUBLE*)pData = pvInvokeResult->dblVal;
                    return TRUE;
                }
                break;

            case CVolUserApp::SUCT_PKG_BOOL:  // 逻辑型类
                if (SUCCEEDED (::VariantChangeType (pvInvokeResult, pvInvokeResult, 0, VT_BOOL)))
                {
                    *(BOOL*)pData = (pvInvokeResult->boolVal != 0);
                    return TRUE;
                }
                break;
            }
        }
        break;  }
    }

    return FALSE;
} */

BOOL_P CVolComObject::InvokeV (const INVOKE_METHOD_TYPE enInvokeType, const TCHAR* szInvokeName,
        VARIANT* pvResult, const INT_P npFirstExtendParamTypeIndex, const TCHAR* szParamTypes, va_list argList)
{
    ASSERT (szParamTypes != NULL && npFirstExtendParamTypeIndex >= 0 && npFirstExtendParamTypeIndex <= (INT_P)_tcslen (szParamTypes));

    if (pvResult != NULL)
        ::VariantInit (pvResult);

    INVOKE_RESULT_TYPE enInvokeResult = IRT_SUCCEEDED;
    IDispatch* pDispatch = NULL;
    ITypeInfo* pTypeInfo = NULL;
    FUNCDESC* pFuncDesc = NULL;
    VARDESC* pVarDesc = NULL;

    CVolMem memNewComParamInfos, memParamVariants;

    do
    {
        if (IsEmptyStr (szInvokeName))
        {
            enInvokeResult = IRT_MEMBER_NOT_FOUND;
            break;
        }

        if (m_pUnknownObject == NULL)
        {
            enInvokeResult = IRT_EMPTY_OBJECT;
            break;
        }

        if (FAILED (m_pUnknownObject->QueryInterface (IID_IDispatch, (void**)&pDispatch)))
        {
            enInvokeResult = IRT_CALLUNABLE;
            break;
        }

        const LCID lcid = GetUserDefaultLCID ();
        ITypeComp* pTypeComp;
        if (FAILED (pDispatch->GetTypeInfo (0, lcid, &pTypeInfo)) ||
                FAILED (pTypeInfo->GetTypeComp (&pTypeComp)))
        {
            enInvokeResult = IRT_TYPE_INFO_NOT_FOUND;
            break;
        }

        WORD waryInvokeFlags [4];
        switch (enInvokeType)
        {
        case IMT_GET_PROPERTY:
            waryInvokeFlags [0] = DISPATCH_PROPERTYGET;
            waryInvokeFlags [1] = DISPATCH_METHOD;
            waryInvokeFlags [2] = 0;
            break;
        case IMT_SET_PROPERTY:
            waryInvokeFlags [0] = DISPATCH_PROPERTYPUT;
            waryInvokeFlags [1] = DISPATCH_PROPERTYPUTREF;
            waryInvokeFlags [2] = DISPATCH_METHOD;
            waryInvokeFlags [3] = 0;
            break;
        case IMT_RUN_METHOD:
            waryInvokeFlags [0] = DISPATCH_METHOD;
            waryInvokeFlags [1] = DISPATCH_PROPERTYGET;
            waryInvokeFlags [2] = DISPATCH_PROPERTYPUT;
            waryInvokeFlags [3] = DISPATCH_PROPERTYPUTREF;
            break;
        default:
            FAIL;
            waryInvokeFlags [0] = 0;
            break;
        }

        pTypeInfo->Release ();
        pTypeInfo = NULL;

        DESCKIND kind;
        BINDPTR bindptr;
        const ULONG lHash = LHashValOfNameSys (SYS_WIN32, lcid, szInvokeName);

        INT_P npIndex;
        for (npIndex = 0; npIndex < (INT_P)sizeof (waryInvokeFlags) / (INT_P)sizeof (waryInvokeFlags [0]); npIndex++)
        {
            if (waryInvokeFlags [npIndex] == 0)
                break;

            if (SUCCEEDED (pTypeComp->Bind ((TCHAR*)szInvokeName, lHash, waryInvokeFlags [npIndex], &pTypeInfo, &kind, &bindptr)) && pTypeInfo != NULL)
                break;

            pTypeInfo = NULL;
        }

        pTypeComp->Release ();

        if (pTypeInfo == NULL)
        {
            enInvokeResult = IRT_MEMBER_NOT_FOUND;
            break;
        }

        DISPID dwDispID;
        INT_P npNumComParams;
        ELEMDESC* pComParamInfo;
        WORD wInvokeFlags;

        if (kind == DESCKIND_FUNCDESC)
        {
            pFuncDesc = bindptr.lpfuncdesc;

            wInvokeFlags = pFuncDesc->invkind;
            npNumComParams = pFuncDesc->cParams;
            pComParamInfo = pFuncDesc->lprgelemdescParam;
            dwDispID = pFuncDesc->memid;
        }
        else if (kind == DESCKIND_VARDESC || kind == DESCKIND_IMPLICITAPPOBJ)
        {
            pVarDesc = bindptr.lpvardesc;

            if (enInvokeType == IMT_SET_PROPERTY)
            {
                npNumComParams = 1;
                pComParamInfo = &pVarDesc->elemdescVar;
                const VARTYPE vtParam = sGetVarType (pTypeInfo, &pComParamInfo->tdesc) & ~VT_BYREF;
                wInvokeFlags = (((vtParam & VT_ARRAY) != 0 || vtParam == VT_UNKNOWN || vtParam == VT_DISPATCH) ?
                        DISPATCH_PROPERTYPUTREF : DISPATCH_PROPERTYPUT);
            }
            else
            {
                wInvokeFlags = DISPATCH_PROPERTYGET;
                npNumComParams = 0;
                pComParamInfo = NULL;
            }

            dwDispID = pVarDesc->memid;
        }
        else
        {
            if (kind == DESCKIND_TYPECOMP)
                bindptr.lptcomp->Release ();

            enInvokeResult = IRT_MEMBER_NOT_FOUND;
            break;
        }

        //----------------------------------------------------------------------

        CVolMem memBuf;
        INVOKE_CALL_PARAM_DATA* pCallParamDataBegin;
        const INT_P npNumCallParams = sParseCallParams (argList, npFirstExtendParamTypeIndex, szParamTypes, &pCallParamDataBegin, memBuf);
        if (npNumCallParams == -1)
        {
            enInvokeResult = IRT_BAD_VAR_TYPE;
            break;
        }

        if (npNumCallParams > npNumComParams)
        {
            if (npNumComParams == 0 || pFuncDesc == NULL || pFuncDesc->cParamsOpt != -1)
            {
                enInvokeResult = IRT_BAD_PARAM_COUNT;
                break;
            }

            ELEMDESC* pComParamInfNew = (ELEMDESC*)memNewComParamInfos.Alloc (sizeof (ELEMDESC) * npNumCallParams);
            COPY_MEM (pComParamInfNew, pComParamInfo, sizeof (ELEMDESC) * npNumComParams);
            pComParamInfo += npNumComParams - 1;
            for (npIndex = npNumComParams; npIndex < npNumCallParams; npIndex++)
                COPY_MEM (pComParamInfNew + npIndex, pComParamInfo, sizeof (ELEMDESC));
            pComParamInfo = pComParamInfNew;
            npNumComParams = npNumCallParams;
        }

        VARIANTARG* pParamVarBegin = (VARIANTARG*)memParamVariants.Alloc (sizeof (VARIANTARG) * npNumCallParams * 2);
        memParamVariants.Zero ();
        VARIANTARG* pParamVarRefDataBegin = pParamVarBegin + npNumCallParams;

        DISPPARAMS dpParams;
        dpParams.rgvarg = pParamVarBegin;
        dpParams.cArgs = (UINT)npNumCallParams;

        DISPID mydispid;
        if ((wInvokeFlags & (DISPATCH_PROPERTYPUT | DISPATCH_PROPERTYPUTREF)) != 0)
        {
            mydispid = DISPID_PROPERTYPUT;
            dpParams.rgdispidNamedArgs = &mydispid;
            dpParams.cNamedArgs = 1;
        }
        else
        {
            dpParams.rgdispidNamedArgs = NULL;
            dpParams.cNamedArgs = 0;
        }

        //----------------------------------------------------------------------

        INVOKE_CALL_PARAM_DATA* pCallParamData = pCallParamDataBegin + npNumCallParams - 1;
        ASSERT (npNumCallParams <= npNumComParams);
        pComParamInfo += npNumCallParams - 1;

        ELEMDESC* pComParamInfBak = pComParamInfo;
        VARIANTARG* pParamVar = pParamVarBegin;
        VARIANTARG* pParamVarRefData = pParamVarRefDataBegin;
        VARIANTARG* pvParam;

        for (npIndex = 0; npIndex < npNumCallParams; npIndex++, pCallParamData--, pComParamInfo--, pParamVar++, pParamVarRefData++)
        {
            const INVOKE_CALL_PARAM_TYPE enParamDataType = pCallParamData->m_enType;

            if (enParamDataType == ICPT_EMPTY)
            {
                pParamVar->vt = VT_ERROR;
                pParamVar->scode = DISP_E_PARAMNOTFOUND;
                continue;
            }

            VARTYPE vtParam = sGetVarType (pTypeInfo, &pComParamInfo->tdesc);
            const BOOL_P blpByRef = ((vtParam & VT_BYREF) != 0);
            const BOOL_P blpIsAry = ((vtParam & VT_ARRAY) != 0);
            vtParam &= VT_TYPEMASK;

            pvParam = (blpByRef ? pParamVarRefData : pParamVar);

            switch (enParamDataType)
            {
            case ICPT_SBYTE:
                pvParam->vt = VT_I1;
                pvParam->cVal = (CHAR)pCallParamData->m_sbyte;
                break;

            case ICPT_SHORT:
                pvParam->vt = VT_I2;
                pvParam->iVal = pCallParamData->m_short;
                break;

            case ICPT_WCHAR:
                pvParam->vt = VT_UI2;
                pvParam->uiVal = (USHORT)pCallParamData->m_char;
                break;

            case ICPT_INT:
                pvParam->vt = VT_I4;
                pvParam->lVal = (long)pCallParamData->m_int;
                break;

            case ICPT_VINT:
            #ifndef _PF_64_BITS
                pvParam->vt = VT_I4;
                pvParam->lVal = (long)pCallParamData->m_vint;
            #else
                pvParam->vt = VT_I8;
                pvParam->llVal = (LONGLONG)pCallParamData->m_vint;
            #endif
                break;

            case ICPT_LONG:
                pvParam->vt = VT_I8;
                pvParam->llVal = (LONGLONG)pCallParamData->m_long;
                break;

            case ICPT_FLOAT:
                pvParam->vt = VT_R4;
                pvParam->fltVal = pCallParamData->m_float;
                break;

            case ICPT_DOUBLE:
                pvParam->vt = VT_R8;
                pvParam->dblVal = pCallParamData->m_double;
                break;

            case ICPT_BOOL:
                pvParam->vt = VT_BOOL;
                pvParam->boolVal = (pCallParamData->m_bool ? VARIANT_TRUE : VARIANT_FALSE);
                break;

            case ICPT_P_SBYTE:
                pvParam->vt = VT_I1;
                pvParam->cVal = (CHAR)*pCallParamData->m_pSByte;
                break;

            case ICPT_P_SHORT:
                pvParam->vt = VT_I2;
                pvParam->iVal = *pCallParamData->m_pShort;
                break;

            case ICPT_P_WCHAR:
                pvParam->vt = VT_UI2;
                pvParam->uiVal = (USHORT)*pCallParamData->m_pChar;
                break;

            case ICPT_P_INT:
                pvParam->vt = VT_I4;
                pvParam->lVal = (long)*pCallParamData->m_pInt;
                break;

            case ICPT_P_VINT:
            #ifndef _PF_64_BITS
                pvParam->vt = VT_I4;
                pvParam->lVal = (long)*pCallParamData->m_pVInt;
            #else
                pvParam->vt = VT_I8;
                pvParam->llVal = (LONGLONG)*pCallParamData->m_pVInt;
            #endif
                break;

            case ICPT_P_LONG:
                pvParam->vt = VT_I8;
                pvParam->llVal = (LONGLONG)*pCallParamData->m_pLong;
                break;

            case ICPT_P_FLOAT:
                pvParam->vt = VT_R4;
                pvParam->fltVal = *pCallParamData->m_pFloat;
                break;

            case ICPT_P_DOUBLE:
                pvParam->vt = VT_R8;
                pvParam->dblVal = *pCallParamData->m_pDouble;
                break;

            case ICPT_P_BOOL:
                pvParam->vt = VT_BOOL;
                pvParam->boolVal = (*pCallParamData->m_pBool ? VARIANT_TRUE : VARIANT_FALSE);
                break;

            case ICPT_P_STRING:
                pvParam->vt = VT_BSTR;
                pvParam->bstrVal = SysAllocString (pCallParamData->m_pStr->GetText ());
                break;

            case ICPT_P_COM_VARIANT:
                VariantCopyInd (pvParam, &pCallParamData->m_pVolComVariant->m_var);
                break;

            case ICPT_P_COM_OBJECT:
                if (pCallParamData->m_pVolComObject->m_pUnknownObject != NULL)
                {
                    if (vtParam == VT_UNKNOWN)
                    {
                        pvParam->vt = VT_UNKNOWN;
                        pvParam->punkVal = pCallParamData->m_pVolComObject->m_pUnknownObject;
                        pvParam->punkVal->AddRef ();
                        break;
                    }
        
                    if (vtParam == VT_DISPATCH)
                    {
                        pvParam->vt = VT_DISPATCH;
                        if (SUCCEEDED (pCallParamData->m_pVolComObject->m_pUnknownObject->QueryInterface (IID_IDispatch, (void**)&pvParam->pdispVal)))
                            break;
                    }
                }

                pvParam->vt = VT_UNKNOWN;
                pvParam->punkVal = NULL;
                break;

            default:
                FAIL;  // 没有其它的类型了
                enInvokeResult = IRT_BAD_VAR_TYPE;
                break;
            }

            if (enInvokeResult != IRT_SUCCEEDED)
                break;

            if (pvParam->vt == VT_EMPTY)
            {
                pParamVar->vt = VT_ERROR;
                pParamVar->scode = DISP_E_PARAMNOTFOUND;
            }
            else if (blpByRef)
            {
                ASSERT (pvParam == pParamVarRefData);

                if (pvParam->vt != VT_ERROR)
                {
                    if (blpIsAry)
                    {
                        if ((pvParam->vt & (VT_ARRAY | VT_BYREF)) == VT_ARRAY)
                        {
                            pParamVar->vt = (pvParam->vt & VT_TYPEMASK) | VT_ARRAY | VT_BYREF;
                            pParamVar->pparray = &pvParam->parray;
                            continue;
                        }
                    }
                    else if (vtParam == VT_VARIANT)
                    {
                        pParamVar->vt = (VT_VARIANT | VT_BYREF);
                        pParamVar->pvarVal = pvParam;
                        continue;
                    }
                    else if (SUCCEEDED (VariantChangeType (pvParam, pvParam, 0, vtParam)))
                    {
                        if (sMakeRefVaiant (pParamVar, pvParam))
                            continue;
                    }
                }

                COPY_MEM (pParamVar, pvParam, sizeof (VARIANTARG));
                VariantInit (pvParam);
            }
            ELSE_ASSERT (pvParam == pParamVar)
        }

        if (enInvokeResult == IRT_SUCCEEDED)
        {
            ASSERT (pDispatch != NULL);

            EXCEPINFO* pinfExcept;
        #ifdef _DEBUG
            EXCEPINFO infExcept;
            ZERO_MEM (&infExcept, sizeof (infExcept));
            pinfExcept = &infExcept;
        #else
            pinfExcept = NULL;
        #endif

            UINT iArgErr = (UINT)-1;
            const HRESULT hr = pDispatch->Invoke (dwDispID, IID_NULL, lcid, wInvokeFlags, &dpParams, pvResult, pinfExcept, &iArgErr);

            if (SUCCEEDED (hr))
            {
                pCallParamData = pCallParamDataBegin + npNumCallParams - 1;
                pParamVar = pParamVarBegin;
                pComParamInfo = pComParamInfBak;

                for (npIndex = 0; npIndex < npNumCallParams; npIndex++, pCallParamData--, pComParamInfo--, pParamVar++)
                {
                    if ((pParamVar->vt & VT_BYREF) != 0 &&
                            // (pComParamInfo->paramdesc.wParamFlags & PARAMFLAG_FOUT) != 0 &&
                            IS_POINTER_CALL_PARAM (pCallParamData->m_enType))
                    {
                        sFillRefParamResult (pCallParamData, pParamVar);
                    }
                }
            }
            else
            {
                enInvokeResult = (hr == DISP_E_BADPARAMCOUNT ? IRT_BAD_PARAM_COUNT :
                        hr == DISP_E_BADVARTYPE ? IRT_BAD_VAR_TYPE :
                        hr == DISP_E_EXCEPTION ? IRT_EXCEPTION :
                        hr == DISP_E_MEMBERNOTFOUND ? IRT_MEMBER_NOT_FOUND :
                        hr == DISP_E_NONAMEDARGS ? IRT_NO_NAMED_ARGS :
                        hr == DISP_E_OVERFLOW ? IRT_OVERFLOW :
                        hr == DISP_E_PARAMNOTFOUND ? IRT_PARAM_NOT_FOUND :
                        hr == DISP_E_TYPEMISMATCH ? IRT_TYPE_MISMATCH :
                        hr == DISP_E_PARAMNOTOPTIONAL ? IRT_PARAM_NOT_OPTIONAL :
                        IRT_CALL_FAILED);

            #ifdef _DEBUG
                ASSERT (pinfExcept == &infExcept);
                if (hr == DISP_E_EXCEPTION)
                {
                    if (infExcept.pfnDeferredFillIn != NULL)
                        infExcept.pfnDeferredFillIn (&infExcept);

                    CVolString strSource;
                    if (::SysStringLen (infExcept.bstrSource))
                        strSource.SetText (infExcept.bstrSource);
                    ::SysFreeString (infExcept.bstrSource);

                    CVolString strDescription;
                    if (::SysStringLen (infExcept.bstrDescription))
                        strDescription.SetText (infExcept.bstrDescription);
                    ::SysFreeString (infExcept.bstrDescription);

                    CVolString strHelpFile;
                    if (::SysStringLen (infExcept.bstrHelpFile))
                        strHelpFile.SetText (infExcept.bstrHelpFile);
                    ::SysFreeString (infExcept.bstrHelpFile);

                    CVolString strDump;
                    strDump.Format (
                        _T ("------ Encounted exception:\r\n")
                            _T ("  Code: %X\r\n")
                            _T ("  Source: %s\r\n")
                            _T ("  Description: %s\r\n")
                            _T ("  HelpFile: %s\r\n")
                            _T ("  HelpContext: %X\r\n")
                            _T ("  scode: %X"),
                        (DWORD)infExcept.wCode,
                        strSource.GetText (),
                        strDescription.GetText (),
                        strHelpFile.GetText (),
                        infExcept.dwHelpContext,
                        (DWORD)infExcept.scode);
                    TRACE0 (strDump.GetText ());
                }
            #endif
            }
        }

        pParamVar = pParamVarBegin;
        for (npIndex = 0; npIndex < npNumCallParams * 2; npIndex++, pParamVar++)
            VariantClear (pParamVar);
    }
    while (FALSE);

    //----------------------------------------------------------------------

    if (pTypeInfo != NULL)
    {
        if (pFuncDesc != NULL)
            pTypeInfo->ReleaseFuncDesc (pFuncDesc);

        if (pVarDesc != NULL)
            pTypeInfo->ReleaseVarDesc (pVarDesc);

        pTypeInfo->Release ();
    }
    ELSE_ASSERT (pFuncDesc == NULL && pVarDesc == NULL)

    if (pDispatch != NULL)
        pDispatch->Release ();

    if (enInvokeResult != IRT_SUCCEEDED && pvResult != NULL)
        ::VariantClear (pvResult);

    m_enInvokeResult = enInvokeResult;
    return (enInvokeResult == IRT_SUCCEEDED);
}

S_BYTE CVolComObject::Invoke_S_BYTE (const INVOKE_METHOD_TYPE enInvokeType, const TCHAR* szInvokeName, const INT_P npFirstExtendParamTypeIndex, const TCHAR* szParamTypes, ...)
{
    va_list argList;
    va_start (argList, szParamTypes);

    S_BYTE res_value = 0;
    VARIANT vResult;
    if (InvokeV (enInvokeType, szInvokeName, &vResult, npFirstExtendParamTypeIndex, szParamTypes, argList))
    {
        if (SUCCEEDED (::VariantChangeType (&vResult, &vResult, 0, VT_I1)))
            res_value = (S_BYTE)vResult.cVal;
        else
            m_enInvokeResult = IRT_GET_RESULT_FAILED;
    }

    ::VariantClear (&vResult);
    va_end (argList);
    return res_value;
}

SHORT CVolComObject::Invoke_SHORT (const INVOKE_METHOD_TYPE enInvokeType, const TCHAR* szInvokeName, const INT_P npFirstExtendParamTypeIndex, const TCHAR* szParamTypes, ...)
{
    va_list argList;
    va_start (argList, szParamTypes);

    SHORT res_value = 0;
    VARIANT vResult;
    if (InvokeV (enInvokeType, szInvokeName, &vResult, npFirstExtendParamTypeIndex, szParamTypes, argList))
    {
        if (SUCCEEDED (::VariantChangeType (&vResult, &vResult, 0, VT_I2)))
            res_value = (SHORT)vResult.iVal;
        else
            m_enInvokeResult = IRT_GET_RESULT_FAILED;
    }

    ::VariantClear (&vResult);
    va_end (argList);
    return res_value;
}

TCHAR CVolComObject::Invoke_TCHAR (const INVOKE_METHOD_TYPE enInvokeType, const TCHAR* szInvokeName, const INT_P npFirstExtendParamTypeIndex, const TCHAR* szParamTypes, ...)
{
    va_list argList;
    va_start (argList, szParamTypes);

    TCHAR res_value = '\0';
    VARIANT vResult;
    if (InvokeV (enInvokeType, szInvokeName, &vResult, npFirstExtendParamTypeIndex, szParamTypes, argList))
    {
        if (SUCCEEDED (::VariantChangeType (&vResult, &vResult, 0, VT_UI2)))
            res_value = (TCHAR)vResult.uiVal;
        else
            m_enInvokeResult = IRT_GET_RESULT_FAILED;
    }

    ::VariantClear (&vResult);
    va_end (argList);
    return res_value;
}

INT CVolComObject::Invoke_INT (const INVOKE_METHOD_TYPE enInvokeType, const TCHAR* szInvokeName, const INT_P npFirstExtendParamTypeIndex, const TCHAR* szParamTypes, ...)
{
    va_list argList;
    va_start (argList, szParamTypes);

    INT res_value = 0;
    VARIANT vResult;
    if (InvokeV (enInvokeType, szInvokeName, &vResult, npFirstExtendParamTypeIndex, szParamTypes, argList))
    {
        if (SUCCEEDED (::VariantChangeType (&vResult, &vResult, 0, VT_I4)))
            res_value = (INT)vResult.lVal;
        else
            m_enInvokeResult = IRT_GET_RESULT_FAILED;
    }

    ::VariantClear (&vResult);
    va_end (argList);
    return res_value;
}

INT64 CVolComObject::Invoke_INT64 (const INVOKE_METHOD_TYPE enInvokeType, const TCHAR* szInvokeName, const INT_P npFirstExtendParamTypeIndex, const TCHAR* szParamTypes, ...)
{
    va_list argList;
    va_start (argList, szParamTypes);

    INT64 res_value = 0;
    VARIANT vResult;
    if (InvokeV (enInvokeType, szInvokeName, &vResult, npFirstExtendParamTypeIndex, szParamTypes, argList))
    {
        if (SUCCEEDED (::VariantChangeType (&vResult, &vResult, 0, VT_I8)))
            res_value = (INT64)vResult.llVal;
        else
            m_enInvokeResult = IRT_GET_RESULT_FAILED;
    }

    ::VariantClear (&vResult);
    va_end (argList);
    return res_value;
}

FLOAT CVolComObject::Invoke_FLOAT (const INVOKE_METHOD_TYPE enInvokeType, const TCHAR* szInvokeName, const INT_P npFirstExtendParamTypeIndex, const TCHAR* szParamTypes, ...)
{
    va_list argList;
    va_start (argList, szParamTypes);

    FLOAT res_value = 0;
    VARIANT vResult;
    if (InvokeV (enInvokeType, szInvokeName, &vResult, npFirstExtendParamTypeIndex, szParamTypes, argList))
    {
        if (SUCCEEDED (::VariantChangeType (&vResult, &vResult, 0, VT_R4)))
            res_value = vResult.fltVal;
        else
            m_enInvokeResult = IRT_GET_RESULT_FAILED;
    }

    ::VariantClear (&vResult);
    va_end (argList);
    return res_value;
}

DOUBLE CVolComObject::Invoke_DOUBLE (const INVOKE_METHOD_TYPE enInvokeType, const TCHAR* szInvokeName, const INT_P npFirstExtendParamTypeIndex, const TCHAR* szParamTypes, ...)
{
    va_list argList;
    va_start (argList, szParamTypes);

    DOUBLE res_value = 0;
    VARIANT vResult;
    if (InvokeV (enInvokeType, szInvokeName, &vResult, npFirstExtendParamTypeIndex, szParamTypes, argList))
    {
        if (SUCCEEDED (::VariantChangeType (&vResult, &vResult, 0, VT_R8)))
            res_value = vResult.dblVal;
        else
            m_enInvokeResult = IRT_GET_RESULT_FAILED;
    }

    ::VariantClear (&vResult);
    va_end (argList);
    return res_value;
}

BOOL CVolComObject::Invoke_BOOL (const INVOKE_METHOD_TYPE enInvokeType, const TCHAR* szInvokeName, const INT_P npFirstExtendParamTypeIndex, const TCHAR* szParamTypes, ...)
{
    va_list argList;
    va_start (argList, szParamTypes);

    BOOL res_value = FALSE;
    VARIANT vResult;
    if (InvokeV (enInvokeType, szInvokeName, &vResult, npFirstExtendParamTypeIndex, szParamTypes, argList))
    {
        if (SUCCEEDED (::VariantChangeType (&vResult, &vResult, 0, VT_BOOL)))
            res_value = (vResult.boolVal != 0);
        else
            m_enInvokeResult = IRT_GET_RESULT_FAILED;
    }

    ::VariantClear (&vResult);
    va_end (argList);
    return res_value;
}

CVolString CVolComObject::Invoke_CVolString (const INVOKE_METHOD_TYPE enInvokeType, const TCHAR* szInvokeName, const INT_P npFirstExtendParamTypeIndex, const TCHAR* szParamTypes, ...)
{
    va_list argList;
    va_start (argList, szParamTypes);

    CVolString res_value;
    VARIANT vResult;
    if (InvokeV (enInvokeType, szInvokeName, &vResult, npFirstExtendParamTypeIndex, szParamTypes, argList))
    {
        if (SUCCEEDED (::VariantChangeType (&vResult, &vResult, 0, VT_BSTR)))
            res_value.SetText (vResult.bstrVal);
        else
            m_enInvokeResult = IRT_GET_RESULT_FAILED;
    }

    ::VariantClear (&vResult);
    va_end (argList);
    return res_value;
}

CVolComVariant CVolComObject::Invoke_CVolComVariant (const INVOKE_METHOD_TYPE enInvokeType, const TCHAR* szInvokeName, const INT_P npFirstExtendParamTypeIndex, const TCHAR* szParamTypes, ...)
{
    va_list argList;
    va_start (argList, szParamTypes);

    CVolComVariant res_value;
    VARIANT vResult;
    if (InvokeV (enInvokeType, szInvokeName, &vResult, npFirstExtendParamTypeIndex, szParamTypes, argList))
        ::VariantCopyInd (&res_value.m_var, &vResult);

    ::VariantClear (&vResult);
    va_end (argList);
    return res_value;
}

CVolComObject CVolComObject::Invoke_CVolComObject (const INVOKE_METHOD_TYPE enInvokeType, const TCHAR* szInvokeName, const INT_P npFirstExtendParamTypeIndex, const TCHAR* szParamTypes, ...)
{
    va_list argList;
    va_start (argList, szParamTypes);

    CVolComObject res_value;
    VARIANT vResult;
    if (InvokeV (enInvokeType, szInvokeName, &vResult, npFirstExtendParamTypeIndex, szParamTypes, argList))
    {
        if (SUCCEEDED (::VariantChangeType (&vResult, &vResult, 0, VT_UNKNOWN)))
            res_value.SetUnknownObject (vResult.punkVal);
        else
            m_enInvokeResult = IRT_GET_RESULT_FAILED;
    }

    ::VariantClear (&vResult);
    va_end (argList);
    return res_value;
}

CVolComObject& CVolComObject::Invoke_ComObject (const INVOKE_METHOD_TYPE enInvokeType, const TCHAR* szInvokeName, CVolComObject& objResult, const INT_P npFirstExtendParamTypeIndex, const TCHAR* szParamTypes, ...)
{
    va_list argList;
    va_start (argList, szParamTypes);

    objResult.ReleaseUnknownObject ();

    VARIANT vResult;
    if (InvokeV (enInvokeType, szInvokeName, &vResult, npFirstExtendParamTypeIndex, szParamTypes, argList))
    {
        if (SUCCEEDED (::VariantChangeType (&vResult, &vResult, 0, VT_UNKNOWN)))
            objResult.SetUnknownObject (vResult.punkVal);
        else
            m_enInvokeResult = IRT_GET_RESULT_FAILED;
    }

    ::VariantClear (&vResult);
    va_end (argList);
    return objResult;
}

BOOL_P CVolComObject::Invoke (const INVOKE_METHOD_TYPE enInvokeType, const TCHAR* szInvokeName, const INT_P npFirstExtendParamTypeIndex, const TCHAR* szParamTypes, ...)
{
    va_list argList;
    va_start (argList, szParamTypes);

    const BOOL_P blpSucceeded = InvokeV (enInvokeType, szInvokeName, NULL, npFirstExtendParamTypeIndex, szParamTypes, argList);

    va_end (argList);
    return blpSucceeded;
}

BOOL_P CVolComObject::sRegOcx (const TCHAR* szOCXFileName, const BOOL_P blpRegister)
{
    if (IsEmptyStr (szOCXFileName))
        return FALSE;

    const HMODULE hLib = LoadLibrary (szOCXFileName);
    if (hLib == NULL)
        return FALSE;

    FARPROC proc = ::GetProcAddress (hLib, (blpRegister ? "DllRegisterServer" : "DllUnregisterServer"));
    if (proc == NULL)
    {
        FreeLibrary (hLib);
        return FALSE;
    }

    proc ();
    FreeLibrary (hLib);
    return TRUE;
}

//------------------------------------------------------------------------------------------------

CComEventHandler::CComEventHandler ()
{
    m_lRefCount = 1;

    m_fnOnComEvent = NULL;
    m_upUserData = 0;

    m_pUnknownObject = NULL;
    m_iidEventSource = IID_NULL;
    m_pIConnectionPoint = NULL;
    m_dwEventCookie = 0;
}

HRESULT STDMETHODCALLTYPE CComEventHandler::QueryInterface (REFIID riid, void** ppvObject)
{
    if (riid == __uuidof (IUnknown))
    {
        *ppvObject = static_cast<IUnknown*> (this);
    }
    else if (riid == __uuidof (IDispatch) || (m_iidEventSource != IID_NULL && riid == m_iidEventSource))
    {
        *ppvObject = static_cast<IDispatch*> (this);
    }
    else
    {
        *ppvObject = NULL;
        return E_NOINTERFACE;
    }

    reinterpret_cast<IUnknown*>(*ppvObject)->AddRef ();
    return S_OK;
}

ULONG STDMETHODCALLTYPE CComEventHandler::AddRef (void)
{
    return ::InterlockedIncrement (&m_lRefCount);
}

ULONG STDMETHODCALLTYPE CComEventHandler::Release (void)
{
    const LONG res = ::InterlockedDecrement (&m_lRefCount);
    if (res == 0)
        delete this;
    return res;
}

HRESULT STDMETHODCALLTYPE CComEventHandler::Invoke (DISPID dispIdMember, REFIID riid, LCID lcid,
        WORD wFlags, DISPPARAMS* pDispParams, VARIANT* pVarResult, EXCEPINFO* pExcepInfo, UINT* puArgErr)
{
    if (m_pUnknownObject == NULL || m_fnOnComEvent == NULL)
        return S_OK;

    CVolComVariant vResult;
    CVolObjectArray aryParamVariants;

    // 获取所有调用参数
    if (pDispParams != NULL && pDispParams->rgvarg != NULL)
    {
        aryParamVariants.InitCount (VOL_RUNTIME_CLASS (CVolComVariant), 0, (INT_P)pDispParams->cArgs);

        INT_P npParamIndex = 0;
        for (INT_P npIndex = (INT_P)pDispParams->cArgs - 1; npIndex >= 0; npIndex--, npParamIndex++)
        {
            // 注意不能使用 VariantCopyInd ,因为可能需要传递回参数值.
            ::VariantCopy (&((CVolComVariant&)aryParamVariants [npParamIndex]).m_var, &pDispParams->rgvarg [npIndex]);
        }
        ASSERT (npParamIndex == aryParamVariants.GetCount ());
    }

    CVolComObject objEventSource;
    objEventSource.SetUnknownObject (m_pUnknownObject);

    // 发送事件
    m_fnOnComEvent (objEventSource, (INT)dispIdMember, aryParamVariants, vResult, m_upUserData);

    if (pVarResult != NULL)
        ::VariantCopyInd (pVarResult, &vResult.m_var);

    return S_OK;
}

BOOL_P CComEventHandler::SetupConnectionPoint (IUnknown* pUnknownObject, const TCHAR* szEventSourceInterfaceName)
{
    IID iidEventSource;
    if (IsEmptyStr (szEventSourceInterfaceName))
    {
        if (sFindDefaultEventSource (pUnknownObject, &iidEventSource) == FALSE)
            return FALSE;
    }
    else
    {
        if (FAILED (szEventSourceInterfaceName [0] == '{' ?
                IIDFromString (szEventSourceInterfaceName, &iidEventSource) :
                CLSIDFromProgID (szEventSourceInterfaceName, &iidEventSource)))
        {
            return FALSE;
        }
    }                                                                                                                                                                

    return SetupConnectionPoint (pUnknownObject, iidEventSource);
}

BOOL_P CComEventHandler::SetupConnectionPoint (IUnknown* pUnknownObject, REFIID riidEventSource)
{
    if (pUnknownObject == NULL || riidEventSource == IID_NULL)
        return FALSE;

    ShutdownConnectionPoint ();

    IConnectionPointContainer* pIConnectionPointContainer;
    if (SUCCEEDED (pUnknownObject->QueryInterface (IID_IConnectionPointContainer, (void**)&pIConnectionPointContainer)))
    {
        IConnectionPoint* pIConnectionPoint;

        if (SUCCEEDED (pIConnectionPointContainer->FindConnectionPoint (riidEventSource, &pIConnectionPoint)))
        {
            pIConnectionPointContainer->Release ();
            m_iidEventSource = riidEventSource;

            DWORD dwEventCookie;
            if (SUCCEEDED (pIConnectionPoint->Advise (static_cast<IUnknown*>(this), &dwEventCookie)))
            {
                m_pUnknownObject = pUnknownObject;
                pUnknownObject->AddRef ();

                m_pIConnectionPoint = pIConnectionPoint;
                m_dwEventCookie = dwEventCookie;
                return TRUE;
            }

            m_iidEventSource = IID_NULL;
            pIConnectionPoint->Release ();
        }
        else
        {
            pIConnectionPointContainer->Release ();
        }
    }

    return FALSE;
}

void CComEventHandler::ShutdownConnectionPoint ()
{
    if (m_pUnknownObject == NULL)
        return;

    ASSERT (m_pIConnectionPoint != NULL);
    m_pIConnectionPoint->Unadvise (m_dwEventCookie);
    m_pIConnectionPoint->Release();
    m_pIConnectionPoint = NULL;

    m_pUnknownObject->Release ();
    m_pUnknownObject = NULL;

    m_iidEventSource = IID_NULL;
    m_dwEventCookie = 0;
}

BOOL_P CComEventHandler::sFindDefaultEventSource (IUnknown* pUnknownObject, IID* piidDefaultEventSource)
{
    ASSERT (piidDefaultEventSource != NULL);

    *piidDefaultEventSource = IID_NULL;

    if (pUnknownObject == NULL)
        return FALSE;

    //--------------------------------------------------------------  从IProvideClassInfo2接口中查找

    LPPROVIDECLASSINFO2 pPCI2 = NULL;

    if (SUCCEEDED (pUnknownObject->QueryInterface (IID_IProvideClassInfo2, (LPVOID*)&pPCI2)))
    {
        ASSERT (pPCI2 != NULL);

        if (SUCCEEDED (pPCI2->GetGUID (GUIDKIND_DEFAULT_SOURCE_DISP_IID, piidDefaultEventSource)))
        {
            ASSERT (IsEqualIID (*piidDefaultEventSource, IID_NULL) == FALSE);

            pPCI2->Release ();
            return (IsEqualIID (*piidDefaultEventSource, IID_NULL) == FALSE);
        }

        ASSERT (IsEqualIID (*piidDefaultEventSource, IID_NULL));
        pPCI2->Release ();
    }

    //--------------------------------------------------------------  从类信息中查找

    LPTYPEINFO pClassInfo = NULL;
    HRESULT hrGetClassInfo = E_FAIL;

    LPPROVIDECLASSINFO pPCI = NULL;
    if (SUCCEEDED (pUnknownObject->QueryInterface (IID_IProvideClassInfo, (LPVOID*)&pPCI)))
    {
        ASSERT (pPCI != NULL);

        hrGetClassInfo = pPCI->GetClassInfo (&pClassInfo);
        pPCI->Release ();
    }

    if (FAILED (hrGetClassInfo) || pClassInfo == NULL)
	{
        IDispatch* pDispatch = NULL;

        if (SUCCEEDED (pUnknownObject->QueryInterface (IID_IDispatch, (LPVOID*)&pDispatch)))
        {
            ASSERT (pDispatch != NULL);

			hrGetClassInfo = pDispatch->GetTypeInfo (0, GetUserDefaultLCID (), &pClassInfo);
            pDispatch->Release ();
        }
	}

    if (SUCCEEDED (hrGetClassInfo) && pClassInfo != NULL)
    {
        LPTYPEATTR pClassAttr;

        if (SUCCEEDED (pClassInfo->GetTypeAttr (&pClassAttr)))
        {
            ASSERT (pClassAttr != NULL);

            INT nFlags;
            HREFTYPE hRefType;

            for (UINT i = 0; i < pClassAttr->cImplTypes; i++)
            {
                if (SUCCEEDED (pClassInfo->GetImplTypeFlags (i, &nFlags)) &&
                        ((nFlags & (IMPLTYPEFLAG_FDEFAULT | IMPLTYPEFLAG_FSOURCE | IMPLTYPEFLAG_FRESTRICTED)) == (IMPLTYPEFLAG_FDEFAULT | IMPLTYPEFLAG_FSOURCE)))
                {
                    LPTYPEINFO pEventInfo = NULL;

                    if (SUCCEEDED (pClassInfo->GetRefTypeOfImplType (i, &hRefType)) &&
                            SUCCEEDED (pClassInfo->GetRefTypeInfo (hRefType, &pEventInfo)))
                    {
                        ASSERT (pEventInfo != NULL);

                        LPTYPEATTR pEventAttr;
                        if (SUCCEEDED (pEventInfo->GetTypeAttr (&pEventAttr)))
                        {
                            ASSERT (pEventAttr != NULL);

                            *piidDefaultEventSource = pEventAttr->guid;
                            pEventInfo->ReleaseTypeAttr (pEventAttr);
                        }

                        pEventInfo->Release ();
                    }

                    break;
                }
            }

            pClassInfo->ReleaseTypeAttr (pClassAttr);
        }

        pClassInfo->Release ();
    }

    //--------------------------------------------------------------  查找第一个事件接口

    if (IsEqualIID (*piidDefaultEventSource, IID_NULL))
    {
		IConnectionPointContainer* pCPC = NULL;

		if (SUCCEEDED (pUnknownObject->QueryInterface (IID_IConnectionPointContainer, (LPVOID*)&pCPC)))
		{
			IEnumConnectionPoints* pECP = NULL;

            ASSERT (pCPC != NULL);
			if (SUCCEEDED (pCPC->EnumConnectionPoints (&pECP)))
			{
				IConnectionPoint* pCP = NULL;

                ASSERT (pECP != NULL);
                if (SUCCEEDED (pECP->Next (1, &pCP, NULL)))
				{
                    ASSERT (pCP != NULL);

					if (FAILED (pCP->GetConnectionInterface (piidDefaultEventSource)))
                        *piidDefaultEventSource = IID_NULL;

                    pCP->Release ();
				}

                pECP->Release ();
			}

            pCPC->Release ();
		}
    }

    return (IsEqualIID (*piidDefaultEventSource, IID_NULL) == FALSE);
}
