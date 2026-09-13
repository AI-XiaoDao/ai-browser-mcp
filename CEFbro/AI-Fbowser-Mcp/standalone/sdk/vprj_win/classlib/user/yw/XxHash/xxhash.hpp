#ifndef PIV_XXHASH_HPP
#define PIV_XXHASH_HPP

#include "..\piv\string.hpp"

#ifndef XXH_INLINE_ALL
#define XXH_INLINE_ALL
#endif
#include "xxhash.h"

namespace piv
{
    namespace hash
    {
        /**
         * @brief 取数据XXH128
         * @tparam T 返回类型(字节集类、文本型)
         * @param input 所欲摘要的数据
         * @param len 数据字节长度
         * @param seed 种子
         * @param rethash 返回的hash值
         * @return hash值
         */
        template <typename T>
        T &Get_XXH128(const void *input, const size_t &len, const uint64_t &seed = 0, T &rethash = T{})
        {
            return piv::encoding::value_to_hex(XXH_INLINE_XXH3_128bits_withSeed(input, len, seed), rethash);
        }
        template <typename T>
        T &Get_XXH128(const ptrdiff_t &input, const size_t &len, const uint64_t &seed = 0, T &rethash = T{})
        {
            return Get_XXH128(reinterpret_cast<const void *>(input), len, seed, rethash);
        }
        template <typename T>
        T &Get_XXH128(const CVolMem &input, const size_t &len = (size_t)-1, const uint64_t &seed = 0, T &rethash = T{})
        {
            return Get_XXH128(input.GetPtr(), len == (size_t)-1 ? static_cast<size_t>(input.GetSize()) : len, seed, rethash);
        }
        template <typename T>
        T &Get_XXH128(const CVolString &input, const size_t &len = (size_t)-1, const uint64_t &seed = 0, T &rethash = T{})
        {
            return Get_XXH128(input.GetText(), len == (size_t)-1 ? input.GetLength() * 2 : len, seed, rethash);
        }
        template <typename T, typename CharT>
        T &Get_XXH128(const std::basic_string<CharT> &input, const size_t &len = (size_t)-1, const uint64_t &seed = 0, T &rethash = T{})
        {
            return Get_XXH128(input.data(), len == (size_t)-1 ? input.size() * sizeof(CharT) : len, seed, rethash);
        }
        template <typename T, typename CharT>
        T &Get_XXH128(const basic_string_view<CharT> &input, const size_t &len = (size_t)-1, const uint64_t &seed = 0, T &rethash = T{})
        {
            return Get_XXH128(input.data(), len == (size_t)-1 ? input.size() * sizeof(CharT) : len, seed, rethash);
        }

        /**
         * @brief 取文件_XXH128
         * @tparam T 返回类型(字节集类、文本型)
         * @param filename 文件名
         * @param off 文件偏移
         * @param len 数据长度
         * @param secret 密码
         * @param seed 种子
         * @param rethash 返回的hash值
         * @return hash值
         */
        template <typename T>
        T &GetFile_XXH128(const wchar_t *filename, int64_t off, uint64_t len, const CVolMem &secret = CVolMem{}, const uint64_t &seed = 0, T &rethash = T{})
        {
            XXH128_hash_t hash = {0};
            FILE *file = NULL;
            file = _wfopen(filename, L"rb");
            if (file)
            {
                if (off > 0)
                    _fseeki64(file, off, SEEK_SET);
                XXH3_state_t *state = XXH_INLINE_XXH3_createState();
                if (secret.GetSize() >= 136)
                    XXH_INLINE_XXH3_128bits_reset_withSecretandSeed(state, secret.GetPtr(), static_cast<size_t>(secret.GetSize()), seed);
                else
                    XXH_INLINE_XXH3_128bits_reset_withSeed(state, seed);
                unsigned char buff[65536];
                size_t rsize = 0;
                while ((rsize = fread(buff, 1, 65536, file)) > 0)
                {
                    if (rsize > len)
                    {
                        XXH_INLINE_XXH3_128bits_update(state, buff, static_cast<size_t>(len));
                        break;
                    }
                    XXH_INLINE_XXH3_128bits_update(state, buff, rsize);
                    len -= rsize;
                }
                hash = XXH_INLINE_XXH3_128bits_digest(state);
                XXH_INLINE_XXH3_freeState(state);
                fclose(file);
            }
            return piv::encoding::value_to_hex(hash, rethash);
        }

    } // namespace hash

} // namespace piv

#endif // PIV_XXHASH_HPP
