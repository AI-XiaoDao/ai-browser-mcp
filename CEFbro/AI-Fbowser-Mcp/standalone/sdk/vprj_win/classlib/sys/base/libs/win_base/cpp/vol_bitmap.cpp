
// Copyright (C) Recursion Company. All rights reserved.

#include "../vol_base.h"

BOOL AlphaStretchBitmap (HDC hdcDest, int nXOriginDest, int nYOriginDest, int nWidthDest, int nHeightDest, HDC hdcBitmap, const BITMAP& infBitmap)
{
    ASSERT (hdcDest != NULL && hdcBitmap != NULL);

    if (infBitmap.bmBitsPixel == 32 && infBitmap.bmBits != NULL)  // dib's bmBits not null.
    {
        BLENDFUNCTION fn;
        fn.BlendOp = AC_SRC_OVER;
        fn.BlendFlags = 0;
        fn.SourceConstantAlpha = 255;
        fn.AlphaFormat = AC_SRC_ALPHA;

        return ::GdiAlphaBlend (hdcDest, nXOriginDest, nYOriginDest, nWidthDest, nHeightDest, hdcBitmap, 0, 0, infBitmap.bmWidth, infBitmap.bmHeight, fn);
    }
    else
    {
        return ::StretchBlt (hdcDest, nXOriginDest, nYOriginDest, nWidthDest, nHeightDest, hdcBitmap, 0, 0, infBitmap.bmWidth, infBitmap.bmHeight, SRCCOPY);
    }
}

/*
转换DDB到DIB步骤: 
    初始化BITMAPINFOHEADER数据结构。 用位图信息决定位图的宽高与字节数。 
    最好使用BI_RGB压缩。 
    实现并选择逻辑调色板。 
    决定位图使用的字节数。首先为BITMAPINFOHEADER和颜色表分配内存，然后调
    用GetDIBits()去计算位图字节数。 
    给最终的位图尺寸分配内存块，包括BITMAPINFOHEADER和颜色表与位图字节数。 
    最终再调用GetDIBits()得到位图的字节数。 
*/

// sDDBToDIB     - Creates a DIB from a DDB
// hBitmap       - Device dependent bitmap
// dwCompression - Type of compression - see BITMAPINFOHEADER
// hPal          - Logical palette
static HANDLE sDDBToDIB (HBITMAP hBitmap, DWORD dwCompression, HPALETTE hPal)
{
    // The function has no arg for bitfields
    if (hBitmap == NULL || dwCompression == BI_BITFIELDS)
        return NULL;

    // Get bitmap information
    BITMAP bm;
    if (::GetObject (hBitmap, sizeof (bm), &bm) == 0)
        return NULL;

    // If a palette has not been supplied use defaul palette
    if (hPal == NULL)
        hPal = (HPALETTE)GetStockObject (DEFAULT_PALETTE);

    // Initialize the bitmapinfoheader
    BITMAPINFOHEADER bi;
    bi.biSize = sizeof (BITMAPINFOHEADER);
    bi.biWidth = bm.bmWidth;
    bi.biHeight = bm.bmHeight;
    bi.biPlanes = 1;
    bi.biBitCount = 24 /*bm.bmPlanes * bm.bmBitsPixel*/;
    bi.biCompression = dwCompression;
    bi.biSizeImage = 0;
    bi.biXPelsPerMeter = 0;
    bi.biYPelsPerMeter = 0;
    bi.biClrUsed = 0;
    bi.biClrImportant = 0;

    // Compute the size of the infoheader and the color table
    int nColors = 0 /*(1 << bi.biBitCount)*/;
    // if (nColors > 256)
    //     nColors = 0;
    DWORD dwLen = bi.biSize + nColors * sizeof (RGBQUAD);

    // We need a device context to get the DIB from
    const HDC hDC = ::GetDC (NULL);
    hPal = SelectPalette (hDC, hPal, FALSE);
    RealizePalette (hDC);

    // Allocate enough memory to hold bitmapinfoheader and color table
    HANDLE hDIB = GlobalAlloc (GMEM_MOVEABLE, dwLen);
    if (hDIB == NULL)
    {
        SelectPalette (hDC, hPal, FALSE);
        ::ReleaseDC (NULL, hDC);
        return NULL;
    }

    LPBITMAPINFOHEADER lpbi = (LPBITMAPINFOHEADER)GlobalLock (hDIB);
    *lpbi = bi;

    // Call GetDIBits with a NULL lpBits param, so the device driver
    // will calculate the biSizeImage field
    GetDIBits (hDC, hBitmap, 0, (DWORD)bi.biHeight, NULL, (LPBITMAPINFO)lpbi, DIB_RGB_COLORS);
    bi = *lpbi;

    // If the driver did not fill in the biSizeImage field, then compute it
    // Each scan line of the image is aligned on a DWORD (32bit) boundary
    if (bi.biSizeImage == 0)
    {
        bi.biSizeImage = ((((bi.biWidth * bi.biBitCount) + 31) & ~31) / 8) * bi.biHeight;

        // If a compression scheme is used the result may infact be larger
        // Increase the size to account for this.
        if (dwCompression != BI_RGB)
            bi.biSizeImage = (bi.biSizeImage * 3) / 2;
    }

    GlobalUnlock (hDIB);

    // Realloc the buffer so that it can hold all the bits
    dwLen += bi.biSizeImage;
    HANDLE handle;
    if (handle = GlobalReAlloc (hDIB, dwLen, GMEM_MOVEABLE))
    {
        hDIB = handle;
    }
    else
    {
        GlobalFree (hDIB);

        SelectPalette (hDC, hPal, FALSE);  // Reselect the original palette
        ::ReleaseDC (NULL, hDC);
        return NULL;
    }

    // Get the bitmap bits
    lpbi = (LPBITMAPINFOHEADER)GlobalLock (hDIB);

    // FINALLY get the DIB
    const BOOL_P blpGotBits = GetDIBits (hDC, hBitmap, 0, (DWORD)bi.biHeight,
            (LPBYTE)lpbi + (bi.biSize + nColors * sizeof (RGBQUAD)), (LPBITMAPINFO)lpbi, DIB_RGB_COLORS);

    SelectPalette (hDC, hPal, FALSE);
    ::ReleaseDC (NULL, hDC);
    GlobalUnlock (hDIB);

    if (blpGotBits == FALSE)
    {
        GlobalFree (hDIB);
        return NULL;
    }

    return hDIB;
}

// sWriteDIB - Writes a DIB to file
// Returns - TRUE on success
// mem - mem to write to
// hDIB - Handle of the DIB
static BOOL_P sWriteDIB (CVolMem& mem, HANDLE hDIB)
{
    mem.Empty ();

    if (hDIB != NULL)
    {
        LPBITMAPINFOHEADER lpbi = (LPBITMAPINFOHEADER)GlobalLock (hDIB);
        int nColors = 1 << lpbi->biBitCount;
        if (nColors > 256)
            nColors = 0;

        // Fill in the fields of the file header
        BITMAPFILEHEADER hdr;
        hdr.bfType = ((WORD)('M' << 8) | 'B'); // is always "BM"
        hdr.bfSize = (DWORD)(GlobalSize (hDIB) + sizeof (hdr));
        hdr.bfReserved1 = 0;
        hdr.bfReserved2 = 0;
        hdr.bfOffBits = (DWORD)(sizeof (hdr) + lpbi->biSize + nColors * sizeof (RGBQUAD));

        // Write the file header
        mem.Append ((LPBYTE)&hdr, sizeof (hdr));

        // Write the DIB header and the bits
        mem.Append ((LPBYTE)lpbi, GlobalSize (hDIB));
        GlobalUnlock (hDIB);
        return TRUE;
    }

    return FALSE;
}

BOOL_P WriteBitmap (HBITMAP hBitmap, CVolMem& mem, INT cx, INT cy)
{
    mem.Empty ();

    if (hBitmap == NULL)
        return FALSE;

    BITMAP bm;
    if (::GetObject (hBitmap, sizeof (bm), &bm) == 0)
        return FALSE;

    CMSize size
    (
        (cx == 0 ? bm.bmWidth : cx < 0 ? MulDiv (bm.bmWidth, MAX (10, -cx), 100) : cx),
        (cy == 0 ? bm.bmHeight : cy < 0 ? MulDiv (bm.bmHeight, MAX (10, -cy), 100) : cy)
    );

    if (size.cx <= 0 || size.cy <= 0)
        return FALSE;

    const HDC hDC = ::GetDC (NULL);

    // 如果设备支持调色板，创建调色板
    HPALETTE hPal;
    if ((::GetDeviceCaps (hDC, RASTERCAPS) & RC_PALETTE) != 0)
    {
        LOGPALETTE* pLP = (LOGPALETTE*)new BYTE [sizeof (LOGPALETTE) + sizeof (PALETTEENTRY) * 256];
        pLP->palVersion = 0x300;
        pLP->palNumEntries = GetSystemPaletteEntries (hDC, 0, 255, pLP->palPalEntry);
        hPal = ::CreatePalette (pLP);  // Create the palette
        delete[] pLP;
    }
    else
        hPal = NULL;

    HANDLE hDIB;
    if (size.cx != bm.bmWidth || size.cy != bm.bmHeight)
    {
        const HDC hDCSrc = ::CreateCompatibleDC (hDC);
        const HBITMAP hOldBitmapSrc = (HBITMAP)::SelectObject (hDCSrc, hBitmap);

        const HBITMAP hNewBitmap = ::CreateCompatibleBitmap (hDC, size.cx, size.cy);

        const HDC hDCDest = CreateCompatibleDC (hDC);
        const HBITMAP hOldBitmapDest = (HBITMAP)::SelectObject (hDCDest, hNewBitmap);

        ::SetStretchBltMode (hDCDest, MGetStretchMode ());
        ::StretchBlt (hDCDest, 0, 0, size.cx, size.cy, hDCSrc, 0, 0, bm.bmWidth, bm.bmHeight, SRCCOPY);

        ::SelectObject (hDCSrc, hOldBitmapSrc);
        ::SelectObject (hDCDest, hOldBitmapDest);
        ::DeleteDC (hDCSrc);
        ::DeleteDC (hDCDest);

        hDIB = sDDBToDIB (hNewBitmap, BI_RGB, hPal);
        ::DeleteObject (hNewBitmap);
    }
    else
    {
        hDIB = sDDBToDIB (hBitmap, BI_RGB, hPal);
    }

    BOOL_P blpResult;
    if (hDIB != NULL)
    {
        blpResult = sWriteDIB (mem, hDIB);
        GlobalFree (hDIB);  // Free the memory allocated by sDDBToDIB for the DIB
    }
    else
        blpResult = FALSE;

    if (hPal != NULL)
        ::DeleteObject (hPal);
    ::ReleaseDC (NULL, hDC);

    return blpResult;
}

static BOOL_P sSaveCatch (HWND hWnd, HDC hWndDC, const CMSize& size, CVolMem& mem, INT cx, INT cy)
{
    if (hWndDC == NULL)
        return FALSE;

    const HBITMAP hBitmap = ::CreateCompatibleBitmap (hWndDC, size.cx, size.cy);

    const HDC hDCMem = ::CreateCompatibleDC (hWndDC);
    const HBITMAP hOldBitmapDest = (HBITMAP)::SelectObject (hDCMem, hBitmap);

    ::BitBlt (hDCMem, 0, 0, size.cx, size.cy, hWndDC, 0, 0, SRCCOPY);

    ::SelectObject (hDCMem, hOldBitmapDest);
    ::DeleteDC (hDCMem);

    const BOOL_P blpResult = WriteBitmap (hBitmap, mem, cx, cy);

    ::DeleteObject (hBitmap);
    ::ReleaseDC (hWnd, hWndDC);

    return blpResult;
}

BOOL_P CatchWindow (HWND hWnd, CVolMem& mem, INT cx, INT cy)
{
    if (hWnd == NULL)
        return FALSE;

    CMRect rect;
    ::GetWindowRect (hWnd, &rect);

    return sSaveCatch (hWnd, ::GetWindowDC (hWnd), rect.Size (), mem, cx, cy);
}

BOOL_P CatchClient (HWND hWnd, CVolMem& mem, INT cx, INT cy)
{
    if (hWnd == NULL)
        return FALSE;

    CMRect rect;
    ::GetClientRect (hWnd, &rect);

    return sSaveCatch (hWnd, ::GetDC (hWnd), rect.Size (), mem, cx, cy);
}

BOOL_P CatchScreen (CVolMem& mem, INT cx, INT cy)
{
    return sSaveCatch (NULL, ::GetDC (NULL), CMSize (GetSystemMetrics (SM_CXSCREEN),
            GetSystemMetrics (SM_CYSCREEN)), mem, cx, cy);
}

HBITMAP CloneBitmap (const HBITMAP hBitmap, INT cx, INT cy)
{
    if (hBitmap == NULL)
        return NULL;

    BITMAP bm;
    if (::GetObject (hBitmap, sizeof (bm), &bm) == 0)
        return NULL;

    cx = (cx == 0 ? bm.bmWidth : cx < 0 ? MulDiv (bm.bmWidth, MAX (10, -cx), 100) : cx);
    cy = (cy == 0 ? bm.bmHeight : cy < 0 ? MulDiv (bm.bmHeight, MAX (10, -cy), 100) : cy);

    if (cx <= 0 || cy <= 0)
        return NULL;

    //----------------------------------------------------------------------------

    const HDC hDC = ::GetDC (NULL);

    const HDC hDCSrc = ::CreateCompatibleDC (hDC);
    const HBITMAP hOldBitmapSrc = (HBITMAP)::SelectObject (hDCSrc, hBitmap);

    const HBITMAP hCloneBitmap = ::CreateCompatibleBitmap (hDC, cx, cy);

    const HDC hDCDest = CreateCompatibleDC (hDC);
    const HBITMAP hOldBitmapDest = (HBITMAP)::SelectObject (hDCDest, hCloneBitmap);

    ::SetStretchBltMode (hDCDest, MGetStretchMode ());
    ::StretchBlt (hDCDest, 0, 0, cx, cy, hDCSrc, 0, 0, bm.bmWidth, bm.bmHeight, SRCCOPY);

    ::SelectObject (hDCSrc, hOldBitmapSrc);
    ::SelectObject (hDCDest, hOldBitmapDest);

    ::DeleteDC (hDCSrc);
    ::DeleteDC (hDCDest);
    ::ReleaseDC (NULL, hDC);

    return hCloneBitmap;
}

static HBITMAP sCatchBitmap (HWND hWnd, HDC hDCSrc, const CMSize& sizeSrc, INT cx, INT cy)
{
    if (hDCSrc == NULL)
        return NULL;

    cx = (cx == 0 ? sizeSrc.cx : cx < 0 ? MulDiv (sizeSrc.cx, MAX (10, -cx), 100) : cx);
    cy = (cy == 0 ? sizeSrc.cy : cy < 0 ? MulDiv (sizeSrc.cy, MAX (10, -cy), 100) : cy);

    if (cx <= 0 || cy <= 0)
    {
        ::ReleaseDC (hWnd, hDCSrc);
        return NULL;
    }

    const HBITMAP hBitmap = ::CreateCompatibleBitmap (hDCSrc, cx, cy);

    const HDC hDCDest = CreateCompatibleDC (hDCSrc);
    const HBITMAP hOldBitmapDest = (HBITMAP)::SelectObject (hDCDest, hBitmap);

    ::SetStretchBltMode (hDCDest, MGetStretchMode ());
    ::StretchBlt (hDCDest, 0, 0, cx, cy, hDCSrc, 0, 0, sizeSrc.cx, sizeSrc.cy, SRCCOPY);

    ::SelectObject (hDCDest, hOldBitmapDest);
    ::DeleteDC (hDCDest);

    ::ReleaseDC (hWnd, hDCSrc);
    return hBitmap;
}

HBITMAP CatchWindowBitmap (HWND hWnd, INT cx, INT cy)
{
    if (hWnd == NULL)
        return NULL;

    CMRect rect;
    ::GetWindowRect (hWnd, &rect);

    return sCatchBitmap (hWnd, ::GetWindowDC (hWnd), rect.Size (), cx, cy);
}

HBITMAP CatchClientBitmap (HWND hWnd, INT cx, INT cy)
{
    if (hWnd == NULL)
        return NULL;

    CMRect rect;
    ::GetClientRect (hWnd, &rect);

    return sCatchBitmap (hWnd, ::GetDC (hWnd), rect.Size (), cx, cy);
}

HBITMAP CatchScreenBitmap (INT cx, INT cy)
{
    return sCatchBitmap (NULL, ::GetDC (NULL), CMSize (GetSystemMetrics (SM_CXSCREEN),
            GetSystemMetrics (SM_CYSCREEN)), cx, cy);
}

/* static BYTE* sReadBitmap (CVolBaseInputStream& stream, UINT* width, UINT* height, CVolMem& memBitmapData)
{
    BITMAP inBM;

    long filesize;
    short res1,res2;
    long pixoff;
    long bmisize;                    
    long compression;
    unsigned long sizeimage;
    long xscale, yscale;
    long colors;
    long impcol;
    DWORD m_bytesRead;

    *width=0; *height=0;

    m_bytesRead = 54;

    BYTE buf [54];
    INT rc=(INT)stream.read (buf, 54);
    if (rc != 54 || buf [0] != 'B' && buf [1] != 'M')
        return NULL;

    filesize = *(long*)&buf[2];
    res1 = *(short*)&buf[6];
    res2 = *(short*)&buf[8];
    pixoff = *(long*)&buf[10];
    bmisize = *(long*)&buf[14];
    inBM.bmWidth = abs (*(long*)&buf[18]);
    inBM.bmHeight = abs (*(long*)&buf[22]);
    inBM.bmPlanes = *(short*)&buf[26];
    inBM.bmBitsPixel = *(short*)&buf[28];
    compression = *(long*)&buf[30];
    sizeimage = *(long*)&buf[34];
    xscale = *(long*)&buf[38];
    yscale = *(long*)&buf[42];
    colors = *(long*)&buf[46];
    impcol = *(long*)&buf[50];

    if (compression!=BI_RGB)
        return NULL;

    if (colors == 0)
        colors = 1 << inBM.bmBitsPixel;

    RGBQUAD *colormap = NULL;

    switch (inBM.bmBitsPixel) {
    case 24:
    case 32:
        break;
    case 1:
    case 4:
    case 8:
        colormap = new RGBQUAD[colors];

        int i;
        for (i=0;i<colors;i++)
        {
            if (stream.read (buf, 4) != 4)
            {
                delete [] colormap;
                return NULL;
            }
            m_bytesRead += 4;

            colormap[i].rgbRed=buf[2];
            colormap[i].rgbGreen=buf[1];
            colormap[i].rgbBlue=buf[0];
        }
        break;
    default:
        return NULL;
    }

    if ((long)m_bytesRead > pixoff)
    {
        if (colormap != NULL)
            delete [] colormap;
        return NULL;
    }
    else if ((long)m_bytesRead < pixoff)
    {
        if (stream.skip (pixoff - m_bytesRead) == FALSE)
        {
            if (colormap != NULL)
                delete [] colormap;
            return NULL;
        }
    }

    m_bytesRead = pixoff;

    int w=inBM.bmWidth;
    int h=inBM.bmHeight;

    *width=w;
    *height=h;

    long row_size = w * 3;

    long bufsize = (long)w * 3 * (long)h;

    BYTE *outBuf = memBitmapData.Alloc (bufsize);

    long row=0;
    long rowOffset=0;
    long offset;
    LPBYTE pLine = NULL;
    
    BYTE fbuf [4096];
    INT np = 0;
    INT nCurSize = 0;
    int nBytes = inBM.bmBitsPixel / 8;
    int nLineSize = w * nBytes;

    for (row=inBM.bmHeight-1;row>=0;row--)
    {
        rowOffset=(long unsigned)row*row_size;                              

        if (inBM.bmBitsPixel==24 || inBM.bmBitsPixel==32)
        {
            if (pLine == NULL)
                pLine = new BYTE [nLineSize];
            if (stream.read (pLine, nLineSize) != nLineSize)
            {
                delete [] pLine;
                memBitmapData.Free ();
                if (colormap != NULL)
                    delete [] colormap;
                return NULL;
            }

            LPBYTE pb = outBuf + rowOffset;
            for (int col=0;col<w;col++)
            {
                offset = col * nBytes;

                *pb++=pLine [offset + 2];
                *pb++=pLine [offset + 1];
                *pb++=pLine [offset];
            }

            m_bytesRead+=nLineSize;
            
            while ((m_bytesRead-pixoff)&3)
            {
                if (stream.skip (1) == FALSE)
                {
                    delete [] pLine;
                    memBitmapData.Free ();
                    if (colormap != NULL)
                        delete [] colormap;
                    return NULL;
                }

                m_bytesRead++;
            }
        }
        else
        {
            int bit_count = 0;
            UINT mask = (1 << inBM.bmBitsPixel) - 1;

            BYTE inbyte=0;

            for (int col=0;col<w;col++)
            {
                int pix=0;

                if (bit_count <= 0)
                {
                    if (np >= nCurSize)
                    {
                        nCurSize = (INT)stream.read (fbuf, sizeof (fbuf));
                        np = 0;
                        if (nCurSize <= 0)
                        {
                            memBitmapData.Free ();
                            if (colormap != NULL)
                                delete [] colormap;
                            return NULL;
                        }
                    }

                    bit_count = 8;
                    inbyte = fbuf [np++];
                    m_bytesRead++;
                }

                bit_count -= inBM.bmBitsPixel;
                pix = ( inbyte >> bit_count) & mask;

                *(outBuf + rowOffset + col * 3 + 2) = colormap[pix].rgbBlue;
                *(outBuf + rowOffset + col * 3 + 1) = colormap[pix].rgbGreen;
                *(outBuf + rowOffset + col * 3 + 0) = colormap[pix].rgbRed;
            }

            while ((m_bytesRead-pixoff)&3)
            {
                if (np >= nCurSize)
                {
                    nCurSize = (INT)stream.read (fbuf, sizeof (fbuf));
                    np = 0;
                    if (nCurSize <= 0)
                    {
                        memBitmapData.Free ();
                        if (colormap != NULL)
                            delete [] colormap;
                        return NULL;
                    }
                }

                np++;
                m_bytesRead++;
            }
        }
    }

    if (pLine != NULL)
        delete [] pLine;
    if (colormap)
        delete [] colormap;

    return outBuf;
}

static BOOL sBGRFromRGB (BYTE *buf, UINT widthPix, UINT height)
{
    if (buf==NULL)
        return FALSE;

    UINT col, row;
    for (row=0;row<height;row++) {
        for (col=0;col<widthPix;col++) {
            LPBYTE pRed, pGrn, pBlu;
            pRed = buf + row * widthPix * 3 + col * 3;
            pGrn = buf + row * widthPix * 3 + col * 3 + 1;
            pBlu = buf + row * widthPix * 3 + col * 3 + 2;

            // swap red and blue
            BYTE tmp;
            tmp = *pRed;
            *pRed = *pBlu;
            *pBlu = tmp;
        }
    }
    return TRUE;
}

static BOOL sVertFlipBuf (BYTE* inbuf, UINT widthBytes, UINT height)
{   
    if (inbuf==NULL)
        return FALSE;

    UINT bufsize=widthBytes;

    BYTE* tb1= (BYTE *)new BYTE[bufsize];
    if (tb1==NULL) {
        return FALSE;
    }

    BYTE* tb2= (BYTE *)new BYTE [bufsize];
    if (tb2==NULL) {
        delete [] tb1;
        return FALSE;
    }
    
    UINT row_cnt;     
    ULONG off1=0;
    ULONG off2=0;

    for (row_cnt=0;row_cnt<(height+1)/2;row_cnt++) {
        off1=row_cnt*bufsize;
        off2=((height-1)-row_cnt)*bufsize;   
        
        memcpy(tb1,inbuf+off1,bufsize);
        memcpy(tb2,inbuf+off2,bufsize);    
        memcpy(inbuf+off1,tb2,bufsize);
        memcpy(inbuf+off2,tb1,bufsize);
    }    

    delete [] tb1;
    delete [] tb2;

    return TRUE;
}

static BYTE* sMakeDwordAlignedBuf (BYTE *dataBuf, UINT widthPix, UINT height, UINT *uiOutWidthBytes, CVolMem& memBuf)
{
    if (dataBuf==NULL)
        return NULL;

    UINT uiWidthBytes = (((widthPix * 24) + 31) / 32 * 4);
    BYTE *pNew = memBuf.Alloc ((INT_P)(UINT_P)(uiWidthBytes * height));
    
    UINT uiInWidthBytes = widthPix * 3, uiCount;
    BYTE* bpInAdd, *bpOutAdd;
    ULONG lInOff, lOutOff;

    for (uiCount=0;uiCount < height;uiCount++)
    {
        lInOff=uiInWidthBytes * uiCount;
        lOutOff=uiWidthBytes * uiCount;

        bpInAdd= dataBuf + lInOff;
        bpOutAdd= pNew + lOutOff;

        memcpy(bpOutAdd,bpInAdd,uiInWidthBytes);
    }

    if (uiOutWidthBytes != NULL)
        *uiOutWidthBytes=uiWidthBytes;
    return pNew;
}

HBITMAP LoadBitmapFromMemory (const BYTE* pBitmapData, const INT_P npBitmapDataSize)
{
    ASSERT_R_ADR (pBitmapData, npBitmapDataSize);

    CVolMem memBuf1, memBuf2;
    UINT uWidth, uHeight;
    CVolMemoryInputStream stream (pBitmapData, npBitmapDataSize);
    BYTE* pb = sReadBitmap (stream, &uWidth, &uHeight, memBuf1);
    if (pb == NULL ||
            sBGRFromRGB (pb, uWidth, uHeight) == FALSE ||
            sVertFlipBuf (pb, uWidth * 3, uHeight) == FALSE)
    {
        return NULL;
    }

    const BYTE* pBuf = sMakeDwordAlignedBuf (pb, uWidth, uHeight, NULL, memBuf2);
    if (pBuf == NULL)
        return FALSE;

    BITMAPINFOHEADER bmiHeader;
    bmiHeader.biSize = sizeof (BITMAPINFOHEADER);
    bmiHeader.biWidth = uWidth;
    bmiHeader.biHeight = uHeight;
    bmiHeader.biPlanes = 1;
    bmiHeader.biBitCount = 24;
    bmiHeader.biCompression = BI_RGB;
    bmiHeader.biSizeImage = 0;
    bmiHeader.biXPelsPerMeter = 0;
    bmiHeader.biYPelsPerMeter = 0;
    bmiHeader.biClrUsed = 0;
    bmiHeader.biClrImportant = 0;

    const HDC hDC = ::GetDC (NULL);
    const HBITMAP hBitmap = CreateDIBitmap (hDC, &bmiHeader, CBM_INIT, pBuf, (BITMAPINFO*)&bmiHeader, DIB_RGB_COLORS);
    ::ReleaseDC (NULL, hDC);

    return hBitmap;
} */

//---------------------------------------------------------------------------------------

#pragma comment (lib, "gdiplus.lib")

BOOL_P CInitGDIPlus::init ()
{
    CMutexLocker locker (m_locker);

    if (m_upToken == 0)
    {
        Gdiplus::GdiplusStartupInput input;
        Gdiplus::GdiplusStartupOutput output;
        ULONG_PTR upToken = 0;
        if (Gdiplus::GdiplusStartup (&upToken, &input, &output) != Gdiplus::Ok)
            return FALSE;

        ASSERT (upToken != 0);
        m_upToken = upToken;
    }

    return TRUE;
}

void CInitGDIPlus::Cleanup ()
{
    CMutexLocker locker (m_locker);

    if (m_upToken != 0)
    {
        Gdiplus::GdiplusShutdown (m_upToken);
        m_upToken = 0;
    }
}

//---------------------------------------------------------------------------------------

void CVolImage::_InitMembers ()
{
	m_hBitmap = NULL;
	m_pBits = NULL;
	m_nWidth = 0;
	m_nHeight = 0;
	m_nPitch = 0;
	m_nBPP = 0;
	m_blHasAlphaChannel = FALSE;
	m_blIsDIBSection = FALSE;
}

CVolImage::~CVolImage ()
{
    Cleanup ();

    // 如果当前为编译DLL,则提前清理GDI+,避免在DllMain中清理(会出错).
    g_objVolApp.DllCleanupGDIPlus ();
}

BOOL_P CVolImage::LoadFromStream (IStream* pStream)
{
    ASSERT_R_DATA_OR_NULL (pStream);

    if (pStream == NULL || g_objVolApp.InitGDIPlus () == FALSE)
        return FALSE;

    Gdiplus::Bitmap bmSrc (pStream);
    return (bmSrc.GetLastStatus () == Gdiplus::Ok ? CreateFromGdiplusBitmap (bmSrc) : FALSE);
}

BOOL_P CVolImage::LoadFromFile (const TCHAR* szFileName)
{
    ASSERT_R_STR_OR_NULL (szFileName);

    if (IsEmptyStr (szFileName) || g_objVolApp.InitGDIPlus () == FALSE)
        return FALSE;

	Gdiplus::Bitmap bmSrc (szFileName);
    return (bmSrc.GetLastStatus () == Gdiplus::Ok ? CreateFromGdiplusBitmap (bmSrc) : FALSE);
}

BOOL_P CVolImage::LoadFromMemory (const void* pImageData, const INT_P npImageDataSize)
{
    if (npImageDataSize <= 0)
        return FALSE;
    ASSERT_R_ADR (pImageData, npImageDataSize);

    const HGLOBAL hMem = ::GlobalAlloc (GMEM_MOVEABLE, (SIZE_T)npImageDataSize);
    if (hMem == NULL)
        return FALSE;

    BOOL_P blpSucceeded = FALSE;

    void* p = ::GlobalLock (hMem);
    if (p != NULL)
    {
        COPY_MEM (p, pImageData, npImageDataSize);
        ::GlobalUnlock (hMem);
    
        blpSucceeded = LoadFromMemory (hMem);
    }

    ::GlobalFree (hMem);
    return blpSucceeded;
}

BOOL_P CVolImage::LoadFromMemory (const HGLOBAL hMem)
{
    if (hMem == NULL)
        return FALSE;

    BOOL_P blpSucceeded = FALSE;

    IStream* pStream;
    if (SUCCEEDED (CreateStreamOnHGlobal (hMem, FALSE, &pStream)))
    {
        blpSucceeded = LoadFromStream (pStream);
        pStream->Release ();
    }

    return blpSucceeded;
}

BOOL_P CVolImage::CreateFromGdiplusBitmap (Gdiplus::Bitmap& bmSrc)
{
	Gdiplus::PixelFormat eSrcPixelFormat = bmSrc.GetPixelFormat ();
	DWORD dwFlags = 0;
	UINT nBPP;
	Gdiplus::PixelFormat eDestPixelFormat;

    const BOOL_P blpIsAlphaPixelFormat = Gdiplus::IsAlphaPixelFormat (eSrcPixelFormat);
	if (blpIsAlphaPixelFormat)
	{
		dwFlags |= createAlphaChannel;
		nBPP = 32;
		eDestPixelFormat = PixelFormat32bppARGB;
	}
    else  // 为了保证绘制时能够正确判断是否具有Alpha通道,所有其它类型图像均转换为24位.
    {
	    if ((eSrcPixelFormat & PixelFormatGDI) != 0)
	    {
		    nBPP = Gdiplus::GetPixelFormatSize (eSrcPixelFormat);
		    eDestPixelFormat = eSrcPixelFormat;

            if (nBPP == 32)
            {
                nBPP = 24;
                eDestPixelFormat = PixelFormat24bppRGB;
            }
        }
        else
        {
	        nBPP = 24;
	        eDestPixelFormat = PixelFormat24bppRGB;
        }
    }

    //---------------------------------------------------------------------

    const INT nSrcImageWidth = bmSrc.GetWidth ();
    const INT nSrcImageHeight = bmSrc.GetHeight ();

	if (Create (nSrcImageWidth, nSrcImageHeight, nBPP, dwFlags) == FALSE)
        return FALSE;

    CVolMem memBuf;
	Gdiplus::ColorPalette* pPalette = NULL;
	if (Gdiplus::IsIndexedPixelFormat (eSrcPixelFormat))
	{
		UINT nPaletteSize = bmSrc.GetPaletteSize ();
        pPalette = (Gdiplus::ColorPalette*)memBuf.Alloc (nPaletteSize);

		bmSrc.GetPalette (pPalette, nPaletteSize);

        if (pPalette->Count <= 0 || pPalette->Count > 256)
            return FALSE;

		RGBQUAD argbPalette [256];
		for (UINT iColor = 0; iColor < pPalette->Count; iColor++)
		{
			Gdiplus::ARGB color = pPalette->Entries [iColor];
			argbPalette [iColor].rgbRed = (BYTE)((color >> RED_SHIFT) & 0xff);
			argbPalette [iColor].rgbGreen = (BYTE)((color >> GREEN_SHIFT) & 0xff);
			argbPalette [iColor].rgbBlue = (BYTE)((color >> BLUE_SHIFT) & 0xff);
			argbPalette [iColor].rgbReserved = 0;
		}

		SetColorTable (0, pPalette->Count, argbPalette);
	}

	if (eDestPixelFormat == eSrcPixelFormat)
	{
		Gdiplus::BitmapData data;
		Gdiplus::Rect rect (0, 0, m_nWidth, m_nHeight);
        if (bmSrc.LockBits (&rect, Gdiplus::ImageLockModeRead, eSrcPixelFormat, &data) != Gdiplus::Ok)
            return FALSE;

        size_t nBytesPerRow = NumberAlignUp (nBPP * m_nWidth, 8) / 8;
		BYTE* pbDestRow = (BYTE*)m_pBits;
		BYTE* pbSrcRow = (BYTE*)data.Scan0;
		for (INT y = 0; y < m_nHeight; y++)
		{
			::memcpy_s (pbDestRow, nBytesPerRow, pbSrcRow, nBytesPerRow);
			pbDestRow += m_nPitch;
			pbSrcRow += data.Stride;
		}

		bmSrc.UnlockBits (&data);
	}
	else
	{
		Gdiplus::Bitmap bmDest (m_nWidth, m_nHeight, m_nPitch, eDestPixelFormat, (BYTE*)m_pBits);
		Gdiplus::Graphics gDest (&bmDest);
        gDest.SetCompositingMode (Gdiplus::CompositingMode::CompositingModeSourceCopy);

		gDest.DrawImage (&bmSrc, 0, 0, nSrcImageWidth, nSrcImageHeight);
    }

    // 如果有Alpha通道,则将所有像素进行预乘处理(GdiAlphaBlend需要).
    if (blpIsAlphaPixelFormat)
    {
        ASSERT (nBPP == 32);

	    BYTE* pbDestRow = (BYTE*)m_pBits;
	    for (INT y = 0; y < m_nHeight; y++)
	    {
            BYTE* pb = pbDestRow;
            for (INT x = 0; x < m_nWidth; x++)
            {
                const INT nAlpha = (INT)(DWORD)pb [3];
                if (nAlpha != 255)
                {
                    for (INT_P npIndex = 0; npIndex < 3; npIndex++)
                        pb [npIndex] = (BYTE)MulDiv ((INT)(DWORD)pb [npIndex], nAlpha, 255);
                }
                pb += 4;
            }
		
		    pbDestRow += m_nPitch;
	    }
    }

    ASSERT (m_hBitmap != NULL);
	return TRUE;
}

BOOL_P CVolImage::CreateEx (INT nWidth, INT nHeight, INT nBPP, DWORD eCompression, const DWORD* pdwBitfields, DWORD dwFlags)
{
	ASSERT (eCompression == BI_RGB || eCompression == BI_BITFIELDS);
    ASSERT ((dwFlags & createAlphaChannel) == 0 || ((nBPP == 32) && (eCompression == BI_RGB)));

    Cleanup ();

    CVolMem memBuf;
	LPBITMAPINFO pbmi = (LPBITMAPINFO)memBuf.Alloc (sizeof (BITMAPINFOHEADER) + sizeof (RGBQUAD) * 256);

	ZERO_MEM (&pbmi->bmiHeader, sizeof (pbmi->bmiHeader));
	pbmi->bmiHeader.biSize = sizeof (pbmi->bmiHeader);
	pbmi->bmiHeader.biWidth = nWidth;
	pbmi->bmiHeader.biHeight = nHeight;
	pbmi->bmiHeader.biPlanes = 1;
	pbmi->bmiHeader.biBitCount = USHORT (nBPP);
	pbmi->bmiHeader.biCompression = eCompression;

	if (nBPP <= 8)
	{
		ASSERT (eCompression == BI_RGB);
        ZERO_MEM (pbmi->bmiColors, 256 * sizeof (RGBQUAD));
	}
	else if (eCompression == BI_BITFIELDS)
	{
		ASSERT (pdwBitfields != NULL);
		::memcpy_s (pbmi->bmiColors, 3 * sizeof (DWORD), pdwBitfields, 3 * sizeof (DWORD));
	}

	const HBITMAP hBitmap = ::CreateDIBSection (NULL, pbmi, DIB_RGB_COLORS, &m_pBits, NULL, 0);
    if (hBitmap == NULL)
        return FALSE;

	Attach (hBitmap, (nHeight < 0 ? DIBOR_TOPDOWN : DIBOR_BOTTOMUP));

	if ((dwFlags & createAlphaChannel) != 0)
		m_blHasAlphaChannel = TRUE;

	return TRUE;
}

void CVolImage::Attach (HBITMAP hBitmap, DIBOrientation eOrientation)
{
	ASSERT (m_hBitmap == NULL && hBitmap != NULL);

	m_hBitmap = hBitmap;
	UpdateBitmapInfo (eOrientation);
}

void CVolImage::UpdateBitmapInfo (DIBOrientation eOrientation)
{
    ASSERT (m_hBitmap != NULL);

	DIBSECTION dibsection;

    const INT_P npNumBytes = ::GetObject (m_hBitmap, sizeof (DIBSECTION), &dibsection);
	if (npNumBytes == (INT)sizeof (DIBSECTION))
	{
		m_blIsDIBSection = TRUE;
		m_nWidth = dibsection.dsBmih.biWidth;
		m_nHeight = abs (dibsection.dsBmih.biHeight);
		m_nBPP = dibsection.dsBmih.biBitCount;
		m_nPitch = ComputePitch (m_nWidth, m_nBPP);
		m_pBits = dibsection.dsBm.bmBits;

		if (eOrientation == DIBOR_DEFAULT)
			eOrientation = ((dibsection.dsBmih.biHeight > 0) ? DIBOR_BOTTOMUP : DIBOR_TOPDOWN);

        if (eOrientation == DIBOR_BOTTOMUP)
		{
			m_pBits = LPBYTE (m_pBits) + ((m_nHeight - 1) * m_nPitch);
			m_nPitch = -m_nPitch;
		}
	}
	else
	{
		ASSERT (npNumBytes == sizeof (BITMAP));

		m_blIsDIBSection = FALSE;
		m_nWidth = dibsection.dsBm.bmWidth;
		m_nHeight = dibsection.dsBm.bmHeight;
		m_nBPP = dibsection.dsBm.bmBitsPixel;
		m_nPitch = 0;
		m_pBits = 0;
	}

	m_blHasAlphaChannel = FALSE;
}

void CVolImage::SetColorTable (UINT iFirstColor, UINT nColors, const RGBQUAD* prgbColors)
{
	ASSERT (m_hBitmap != NULL && m_blIsDIBSection && IsIndexed ());

	const HDC hDC = ::CreateCompatibleDC (NULL);
    const HBITMAP hOldBitmap = (HBITMAP)::SelectObject (hDC, m_hBitmap);

	::SetDIBColorTable (hDC, iFirstColor, nColors, prgbColors);

    ::SelectObject (hDC, hOldBitmap);
	::DeleteDC (hDC);
}
