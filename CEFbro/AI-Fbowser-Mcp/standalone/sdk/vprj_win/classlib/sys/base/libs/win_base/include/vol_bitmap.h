
#ifndef __VOL_BITMAP_H__
#define __VOL_BITMAP_H__

// 下列函数中的 cx 和 cy 参数:
//   提供图片的输出尺寸.
//   如果cx或者cy小于0,则表示为相应宽度或高度的源图片尺寸百分比(百分比最小为10%).
//   如果cx或者cy等于0,则表示相应宽度或高度使用源图片对应原有尺寸.
//   如果cx或者cy大于0,则表示相应宽度或高度使用指定尺寸.

BOOL_P WriteBitmap (HBITMAP hBitmap, CVolMem& mem, INT cx, INT cy);
BOOL_P CatchWindow (HWND hWnd, CVolMem& mem, INT cx, INT cy);
BOOL_P CatchClient (HWND hWnd, CVolMem& mem, INT cx, INT cy);
BOOL_P CatchScreen (CVolMem& mem, INT cx, INT cy);
HBITMAP CloneBitmap (const HBITMAP hBitmap, INT cx, INT cy);
HBITMAP CatchWindowBitmap (HWND hWnd, INT cx, INT cy);
HBITMAP CatchClientBitmap (HWND hWnd, INT cx, INT cy);
HBITMAP CatchScreenBitmap (INT cx, INT cy);
// HBITMAP LoadBitmapFromMemory (const BYTE* pBitmapData, const INT_P npBitmapDataSize);
HIMAGELIST CreateImageListFromBitmapData (const BYTE* pBitmapData, const INT_P npBitmapDataSize);

inline_ HIMAGELIST CreateImageListFromBitmapData (const CVolMem& memBitmapData)
{
    return CreateImageListFromBitmapData (memBitmapData.GetPtr (), memBitmapData.GetSize ());
}

/* inline_ HBITMAP LoadBitmapFromMemory (const CVolMem& memBitmapData)
{
    return LoadBitmapFromMemory (memBitmapData.GetPtr (), memBitmapData.GetSize ());
} */

BOOL AlphaStretchBitmap (HDC hdcDest, int nXOriginDest, int nYOriginDest, int nWidthDest, int nHeightDest, HDC hdcBitmap, const BITMAP& infBitmap);

//--------------------------------------------------------------------------------

class CInitGDIPlus : public CVolCommonBase
{
public:
    inline_ CInitGDIPlus ()
    {
        m_upToken = 0;
    }

    inline_ ~CInitGDIPlus ()
    {
        Cleanup ();
    }

    BOOL_P init ();
    void Cleanup ();

protected:
    CMMutex m_locker;
	ULONG_PTR m_upToken;
};

//--------------------------------------------------------------------------------

__pragma (warning (push))
__pragma (warning (disable: 6385))
#include <gdiplus.h>
__pragma (warning (pop))

class CVolImage : public CVolCommonBase
{
public:
    inline_ CVolImage ()
    {
        _InitMembers ();
    }

    ~CVolImage ();

    inline_ void Cleanup ()
    {
        if (m_hBitmap != NULL)
            ::DeleteObject (Detach ());
    }

public:
    BOOL_P LoadFromStream (IStream* pStream);
    BOOL_P LoadFromFile (const TCHAR* szFileName);
    BOOL_P LoadFromMemory (const void* pImageData, const INT_P npImageDataSize);
    BOOL_P LoadFromMemory (const HGLOBAL hMem);

    inline_ HBITMAP Detach ()
    {
	    const HBITMAP hBitmap = m_hBitmap;
        _InitMembers ();
	    return hBitmap;
    }

    inline_ HBITMAP GetBitmapHandle () const
    {
	    return m_hBitmap;
    }

    inline_ BOOL_P IsEmpty () const
    {
	    return (m_hBitmap == NULL);
    }

    inline_ BOOL_P IsIndexed () const
    {
	    return (m_nBPP <= 8);
    }

    inline_ INT GetWidth () const
    {
	    return m_nWidth;
    }

    inline_ INT GetHeight () const
    {
	    return m_nHeight;
    }

protected:
    void _InitMembers ();
    BOOL_P CreateFromGdiplusBitmap (Gdiplus::Bitmap& bmSrc);

	static const DWORD createAlphaChannel = 0x01;

    enum DIBOrientation
    {
        DIBOR_DEFAULT,
        DIBOR_TOPDOWN,
        DIBOR_BOTTOMUP
    };

    inline_ BOOL_P Create (INT nWidth, INT nHeight, INT nBPP, DWORD dwFlags)
    {
        return CreateEx (nWidth, nHeight, nBPP, BI_RGB, NULL, dwFlags);
    }
    BOOL_P CreateEx (INT nWidth, INT nHeight, INT nBPP, DWORD eCompression, const DWORD* pdwBitfields, DWORD dwFlags);
    void Attach (HBITMAP hBitmap, DIBOrientation eOrientation);
    void UpdateBitmapInfo (DIBOrientation eOrientation);
    void SetColorTable (UINT iFirstColor, UINT nColors, const RGBQUAD* prgbColors);

	inline_ static INT ComputePitch (int nWidth, int nBPP)
	{
		return (((nWidth * nBPP) + 31) / 32) * 4;
	}

protected:
	HBITMAP m_hBitmap;
	void* m_pBits;
	INT m_nWidth, m_nHeight, m_nPitch, m_nBPP;
	BOOL m_blHasAlphaChannel, m_blIsDIBSection;
};

#endif
