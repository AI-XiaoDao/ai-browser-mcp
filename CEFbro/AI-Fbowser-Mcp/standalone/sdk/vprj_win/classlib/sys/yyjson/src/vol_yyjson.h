#ifndef VOL_YYJSON_H
#define VOL_YYJSON_H

#include "yyjson.h"

class CJsonObjectKeyTextData : public CVolCommonBaseWithMemManager
{
	public:
		~CJsonObjectKeyTextData() 
		{
			U8CHAR** data = (U8CHAR**)m_mem.GetPtr();
			const INT_P len = m_mem.GetSize () / sizeof (U8CHAR*);
			for (INT_P i = 0; i < len; i++)
			{
				if (data [i] != NULL)
					mgrFree (data [i]);
			}
		}
	
		U8CHAR* CloneText (const U8CHAR* szText)
		{
			if (szText == NULL || *szText == '\0')
				return NULL;
			INT_P strLen = strlen (szText);
			U8CHAR* szNew = (U8CHAR*)mgrAlloc ((strLen + 1) * sizeof (U8CHAR));
			COPY_MEM (szNew, szText, strLen * sizeof (U8CHAR));
			szNew [strLen] = '\0';
			m_mem.Append(&szNew, sizeof (U8CHAR*));
			return szNew;
		}
		
	private:
		CVolMem m_mem;
};

class CRefJsonObjectPtrWithData : public CRefObject
{
	public:
		inline_ CRefJsonObjectPtrWithData () { this->m_data = NULL; }
		inline_ void SetData (yyjson_doc *data) { if (this->m_data) yyjson_doc_free(this->m_data); this->m_data = data; }
		inline_ yyjson_doc *GetData () { return this->m_data; } 
		virtual void OnBeforeDestory () override { if (this->m_data) { yyjson_doc_free(this->m_data); this->m_data = NULL; } }
		virtual ~CRefJsonObjectPtrWithData () { if (this->m_data) yyjson_doc_free(this->m_data); }

	public:
		yyjson_doc *m_data;
};

class CRefJsonMutObjectPtrWithData : public CRefObject
{
	public:
		inline_ CRefJsonMutObjectPtrWithData () { this->m_data = yyjson_mut_doc_new(NULL); }
		inline_ void SetData (yyjson_mut_doc *data) { if (this->m_data) yyjson_mut_doc_free(this->m_data); this->m_data = data; }
		inline_ yyjson_mut_doc *GetData () { return this->m_data; } 
		virtual void OnBeforeDestory () override { if (this->m_data) { yyjson_mut_doc_free(this->m_data); this->m_data = NULL; } }
		virtual ~CRefJsonMutObjectPtrWithData () { if (this->m_data) yyjson_mut_doc_free(this->m_data); }

	public:
		yyjson_mut_doc *m_data;
};

class CVolJsonObject
{
	private:
		CRefJsonObjectPtrWithData *pRefObject;
		yyjson_val *docRoot;
		
	public:
		inline_ CVolJsonObject (){ this->pRefObject = new CRefJsonObjectPtrWithData; this->docRoot = NULL; }
		inline_ ~CVolJsonObject (){ if (this->pRefObject) this->pRefObject->Release(); }
		
		inline_ BOOL CreateFromMem(CVolMem& json) { return CreateDoc((const char*)json.GetPtr(), json.GetSize()); }
		
		inline_ BOOL CreateFromText(CVolString& json)
		{
			CU8String u8str(json.GetText());
			const U8CHAR* ps = u8str.GetText ();
			return CreateDoc(ps, strlen(ps));
		}
		
		inline_ BOOL CreateFromFile(CVolString& path) 
		{
			this->pRefObject->SetData(yyjson_read_file(GetMbsText(path.GetText(), CVolMem(), NULL), 0, NULL, NULL));
			return GetObject() != NULL;
		}

	private:
		BOOL CreateDoc(const char* dat, size_t len)
		{
			this->pRefObject->SetData(yyjson_read(dat, len, 0));
			return GetObject() != NULL;
		}

	public:	
		yyjson_val* GetObject()
		{
			if (GetDoc())
			{
				if (this->docRoot == NULL)
					this->docRoot = yyjson_doc_get_root(GetDoc());
			}
			return this->docRoot;
		}
		
		inline_ yyjson_doc* GetDoc()
		{
			return this->pRefObject->m_data;
		}
		
		inline_ CRefJsonObjectPtrWithData* GetRefObject()
		{
			return this->pRefObject;
		}
		
		void SetObject(yyjson_val* obj, CRefJsonObjectPtrWithData *pRef)
		{
			this->docRoot = obj;
			ASSERT(pRef != NULL);
			if (pRef) pRef->AddRef();
			if (this->pRefObject) this->pRefObject->Release();
			this->pRefObject = pRef;
		}
		
		CVolString ToString(yyjson_write_flag flg)
		{
			if (GetObject())
			{
				if (yyjson_doc_get_root(GetDoc()) == GetObject())
				{
					char* jsonString = yyjson_write(GetDoc(), flg, NULL);
					CVolString ret((const CHAR*)jsonString);
					free(jsonString);
					return ret;
				}
				yyjson_mut_doc *tempMutDoc = yyjson_mut_doc_new(NULL);
				yyjson_mut_val *tempMutVal = yyjson_val_mut_copy(tempMutDoc, GetObject());
				yyjson_mut_doc_set_root(tempMutDoc, tempMutVal);
				char* jsonString = yyjson_mut_write(tempMutDoc, flg, NULL);
				CVolString ret((const CHAR*)jsonString);
				free(jsonString);
				yyjson_mut_doc_free(tempMutDoc);
				return ret;
			}
			return _T("");
		}
};

class CVolJsonArray
{
	private:
		CRefJsonObjectPtrWithData *pRefObject;
		yyjson_val *array;
		
	public:
		inline_ CVolJsonArray (){ this->array = NULL; this->pRefObject = NULL; }
		inline_ ~CVolJsonArray (){ if (this->pRefObject) this->pRefObject->Release(); }

		inline_ yyjson_val* GetArray()
		{
			return this->array;
		}
		
		inline_ yyjson_doc* GetDoc()
		{
			return (this->pRefObject ? this->pRefObject->m_data : NULL);
		}
		
		inline_ CRefJsonObjectPtrWithData* GetRefObject()
		{
			return this->pRefObject;
		}
		
		void SetArray(yyjson_val* arr, CRefJsonObjectPtrWithData *pRef)
		{
			this->array = arr;
			ASSERT(pRef != NULL);
			if (pRef) pRef->AddRef();
			if (this->pRefObject) this->pRefObject->Release();
			this->pRefObject = pRef;
		}
		
		CVolString ToString(yyjson_write_flag flg)
		{
			if (GetArray())
			{
				if (yyjson_doc_get_root(GetDoc()) == GetArray())
				{
					char* jsonString = yyjson_write(GetDoc(), flg, NULL);
					CVolString ret((const CHAR*)jsonString);
					free(jsonString);
					return ret;
				}
				yyjson_mut_doc *tempMutDoc = yyjson_mut_doc_new(NULL);
				yyjson_mut_val *tempMutVal = yyjson_val_mut_copy(tempMutDoc, GetArray());
				yyjson_mut_doc_set_root(tempMutDoc, tempMutVal);
				char* jsonString = yyjson_mut_write(tempMutDoc, flg, NULL);
				CVolString ret((const CHAR*)jsonString);
				free(jsonString);
				yyjson_mut_doc_free(tempMutDoc);
				return ret;
			}
			return _T("");
		}
};

class CVolJsonMutObject
{
	private:
		CRefJsonMutObjectPtrWithData *pRefObject;
		yyjson_mut_val *docRoot;
		CJsonObjectKeyTextData keys;
		
	public:
		inline_ CVolJsonMutObject ()
		{ 
			this->pRefObject = new CRefJsonMutObjectPtrWithData; 
			this->docRoot = NULL;
		}
		
		inline_ ~CVolJsonMutObject (){ if (this->pRefObject) this->pRefObject->Release(); }
		
		inline_ BOOL CreateFromMem(CVolMem& json) { return CreateDoc((const char*)json.GetPtr(), json.GetSize()); }
		
		inline_ BOOL CreateFromText(CVolString& json)
		{
			CU8String u8str(json.GetText());
			const U8CHAR* ps = u8str.GetText ();
			return CreateDoc(ps, strlen(ps));
		}
		
		inline_ BOOL CreateFromFile(CVolString& path) 
		{
			yyjson_doc *tempDoc = yyjson_read_file(GetMbsText(path.GetText(), CVolMem(), NULL), 0, NULL, NULL);
			yyjson_mut_doc *tempMutDoc = yyjson_mut_doc_new(NULL);
			
			if (tempDoc && tempMutDoc)
			{
				this->docRoot = yyjson_val_mut_copy(tempMutDoc, yyjson_doc_get_root(tempDoc));
				yyjson_mut_doc_set_root(tempMutDoc, this->docRoot);
				this->pRefObject->SetData(tempMutDoc);
				if (tempDoc) yyjson_doc_free(tempDoc);
				return TRUE;
			}
			
			if (tempDoc) yyjson_doc_free(tempDoc);
			if (tempMutDoc) yyjson_mut_doc_free(tempMutDoc);
			return FALSE;
		}

	private:	
		BOOL CreateDoc(const char* dat, size_t len)
		{
			yyjson_doc *tempDoc = yyjson_read(dat, len, 0);
			yyjson_mut_doc *tempMutDoc = yyjson_mut_doc_new(NULL);
			if (tempDoc && tempMutDoc)
			{
				this->docRoot = yyjson_val_mut_copy(tempMutDoc, yyjson_doc_get_root(tempDoc));
				yyjson_mut_doc_set_root(tempMutDoc, this->docRoot);
				this->pRefObject->SetData(tempMutDoc);
				if (tempDoc) yyjson_doc_free(tempDoc);
				return TRUE;
			}
			if (tempDoc) yyjson_doc_free(tempDoc);
			if (tempMutDoc) yyjson_mut_doc_free(tempMutDoc);
			return FALSE;
		}

	public:	
		inline_ const U8CHAR* CloneKey(CVolString& key) { return keys.CloneText(CU8String(key.GetText()).GetText()); }
		
		yyjson_mut_val* GetObject()
		{
			if (GetDoc())
			{
				if (this->docRoot == NULL)
				{
					yyjson_mut_val* tempObj = yyjson_mut_doc_get_root(this->pRefObject->m_data);
					if (tempObj)
						this->docRoot = tempObj;
					else
					{
						this->docRoot = yyjson_mut_obj(GetDoc());
						yyjson_mut_doc_set_root(this->pRefObject->m_data, this->docRoot);
					}
				}
			}
			return this->docRoot;
		}
		
		inline_ yyjson_mut_doc* GetDoc()
		{
			return this->pRefObject->m_data;
		}
		
		inline_ CRefJsonMutObjectPtrWithData* GetRefObject()
		{
			return this->pRefObject;
		}
		
		inline_ BOOL CreateObject(yyjson_mut_val* obj)
		{
			if (!this->docRoot && obj) 
			{
				this->docRoot = obj;
				return TRUE;
			}
			return FALSE;
		}
		
		void SetObject(yyjson_mut_val* obj, CRefJsonMutObjectPtrWithData *pRef)
		{
			this->docRoot = obj;
			ASSERT(pRef != NULL);
			if (pRef) pRef->AddRef();
			if (this->pRefObject) this->pRefObject->Release();
			this->pRefObject = pRef;
		}
		
		CVolString ToString(yyjson_write_flag flg)
		{
			if (GetObject())
			{
				if (yyjson_mut_doc_get_root(GetDoc()) == GetObject())
				{
					char* jsonString = yyjson_mut_write(GetDoc(), flg, NULL);
					CVolString ret((const CHAR*)jsonString);
					free(jsonString);
					return ret;
				}
				yyjson_mut_doc *tempMutDoc = yyjson_mut_doc_new(NULL);
				yyjson_mut_doc_set_root(tempMutDoc, GetObject());
				char* jsonString = yyjson_mut_write(tempMutDoc, flg, NULL);
				CVolString ret((const CHAR*)jsonString);
				free(jsonString);
				yyjson_mut_doc_free(tempMutDoc);
				return ret;
			}
			return _T("");
		}
};

class CVolJsonMutArray
{
	private:
		CRefJsonMutObjectPtrWithData *pRefObject;
		yyjson_mut_val *array;
		
	public:
		inline_ CVolJsonMutArray ()
		{
			this->pRefObject = new CRefJsonMutObjectPtrWithData;
			this->array = NULL;
		}
		
		inline_ ~CVolJsonMutArray (){ if (this->pRefObject) this->pRefObject->Release(); }

		yyjson_mut_val* GetArray()
		{
			if (GetDoc())
			{
				if (this->array == NULL)
				{
					yyjson_mut_val* tempArray = yyjson_mut_doc_get_root(this->pRefObject->m_data);
					if (tempArray)
						this->array = tempArray;
					else
					{
						this->array = yyjson_mut_arr(GetDoc());
						yyjson_mut_doc_set_root(this->pRefObject->m_data, this->array);
					}
				}
			}
			return this->array;
		}
		
		inline_ yyjson_mut_doc* GetDoc()
		{
			return (this->pRefObject ? this->pRefObject->m_data : NULL);
		}
		
		inline_ CRefJsonMutObjectPtrWithData* GetRefObject()
		{
			return this->pRefObject;
		}
		
		inline_ BOOL CreateArray(yyjson_mut_val* arr)
		{
			if (!this->array && arr) 
			{
				this->array = arr;
				return TRUE;
			}
			return FALSE;
		}
		
		void SetArray(yyjson_mut_val* arr, CRefJsonMutObjectPtrWithData *pRef)
		{
			this->array = arr;
			ASSERT(pRef != NULL);
			if (pRef) pRef->AddRef();
			if (this->pRefObject) this->pRefObject->Release();
			this->pRefObject = pRef;
		}
		
		CVolString ToString(yyjson_write_flag flg)
		{
			if (GetArray())
			{
				if (yyjson_mut_doc_get_root(GetDoc()) == GetArray())
				{
					char* jsonString = yyjson_mut_write(GetDoc(), flg, NULL);
					CVolString ret((const CHAR*)jsonString);
					free(jsonString);
					return ret;
				}
				yyjson_mut_doc *tempMutDoc = yyjson_mut_doc_new(NULL);
				yyjson_mut_doc_set_root(tempMutDoc, GetArray());
				char* jsonString = yyjson_mut_write(tempMutDoc, flg, NULL);
				CVolString ret((const CHAR*)jsonString);
				free(jsonString);
				yyjson_mut_doc_free(tempMutDoc);
				return ret;
			}
			return _T("");
		}
};

#endif /* VOL_YYJSON_H */
