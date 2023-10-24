#pragma once
#include "array2D.h"

namespace GNNBEM
{

template <typename T>
class GArr3D;
template <typename T>
class CArr3D;

template <typename T>
class GArr3D
{
    public:
        GArr<T> data;
        int batchs, rows, cols;
        int3 size;
        void resize(int batchs, int rows, int cols)
        {
            this->rows = rows;
            this->cols = cols;
            this->batchs = batchs;
            size = make_int3(batchs, rows, cols);
            this->data.resize(rows * cols * batchs);
        }

        void resize(int3 size) { resize(size.x, size.y, size.z); }
        GArr3D() { resize(0, 0, 0); }
        GArr3D(int batchs, int rows, int cols) { this->resize(batchs, rows, cols); }
        GArr3D(CArr3D<T> &A) { this->assign(A); }
        void assign(const CArr3D<T> &A)
        {
            this->rows = A.rows;
            this->cols = A.cols;
            this->batchs = A.batchs;
            size = make_int3(batchs, rows, cols);
            data.assign(A.data);
        }

        void assign(const GArr3D<T> &A)
        {
            this->rows = A.rows;
            this->cols = A.cols;
            this->batchs = A.batchs;
            size = make_int3(batchs, rows, cols);
            data.assign(A.data);
        }

        void clear() { data.clear(); }
        void reset() { data.reset(); }
        void reset_minus_one() { data.reset_minus_one(); }
        ~GArr3D(){};
        GPU_FUNC inline const T &operator()(const uint b_i, const uint i, const uint j) const
        {
            return data[b_i * rows * cols + i * cols + j];
        }

        GPU_FUNC inline T &operator()(const uint b_i, const uint i, const uint j)
        {
            return data[b_i * rows * cols + i * cols + j];
        }

        CPU_FUNC inline const T operator()(const to_cpu idx) const
        {
            return data[to_cpu(idx.x * rows * cols + idx.y * cols + idx.z)];
        }

        CPU_FUNC inline T operator()(const to_cpu idx)
        {
            return data[to_cpu(idx.x * rows * cols + idx.y * cols + idx.z)];
        }

        GPU_FUNC inline const T &operator()(const int3 index) const
        {
            return data[index.x * rows * cols + index.y * cols + index.z];
        }

        GPU_FUNC inline T &operator()(const int3 index)
        {
            return data[index.x * rows * cols + index.y * cols + index.z];
        }

        CGPU_FUNC inline int index(const uint b_i, const uint i, const uint j) const
        {
            return b_i * rows * cols + i * cols + j;
        }

        inline GArr2D<T> operator[](unsigned int id) { return GArr2D<T>(data.data() + id * rows * cols, rows, cols); }

        inline const GArr2D<T> operator[](unsigned int id) const
        {
            return GArr2D<T>(data.data() + id * rows * cols, rows, cols);
        }

        CGPU_FUNC inline const T *begin() const { return data.begin(); }
        CGPU_FUNC inline const T *end() const { return data.end(); }
        CGPU_FUNC inline T *begin() { return data.begin(); }
        CGPU_FUNC inline T *end() { return data.end(); }

        inline CArr3D<T> cpu() { return CArr3D<T>(*this); }

        friend std::ostream &operator<<(std::ostream &os, GArr3D<T> &mat)
        {
            os << mat.cpu();
            return os;
        }
};

template <typename T>
class CArr3D
{
    public:
        CArr<T> data;
        int batchs, rows, cols;
        int3 size;
        CArr3D() {}
        void resize(int batchs, int rows, int cols)
        {
            this->rows = rows;
            this->cols = cols;
            this->batchs = batchs;
            size = make_int3(batchs, rows, cols);
            this->data.resize(rows * cols * batchs);
        }
        CArr3D(int batchs, int rows, int cols) { this->resize(batchs, rows, cols); }
        CArr3D(GArr3D<T> &A) { this->assign(A); }
        void assign(GArr3D<T> &A)
        {
            this->rows = A.rows;
            this->cols = A.cols;
            this->batchs = A.batchs;
            size = make_int3(batchs, rows, cols);
            data.assign(A.data);
        }
        void clear() { data.clear(); }
        void reset() { data.reset(); }
        void reset_minus_one() { data.reset_minus_one(); }
        inline const T &operator()(const uint b_i, const uint i, const uint j) const
        {
            return data[b_i * rows * cols + i * cols + j];
        }

        inline T &operator()(const uint b_i, const uint i, const uint j)
        {
            return data[b_i * rows * cols + i * cols + j];
        }

        inline const T &operator()(const int3 index) const
        {
            return data[index.x * rows * cols + index.y * cols + index.z];
        }

        inline T &operator()(const int3 index) { return data[index.x * rows * cols + index.y * cols + index.z]; }

        inline CArr2D<T> operator[](unsigned int id) { return CArr2D<T>(data.data() + id * rows * cols, rows, cols); }

        inline const CArr2D<T> operator[](unsigned int id) const
        {
            return CArr2D<T>(data.data() + id * rows * cols, rows, cols);
        }

        inline int index(const uint b_i, const uint i, const uint j) const { return b_i * rows * cols + i * cols + j; }

        friend std::ostream &operator<<(std::ostream &os, const CArr3D<T> &mat)
        {
            for (int i = 0; i < mat.batchs; i++)
            {
                for (int j = 0; j < mat.rows; j++)
                {
                    for (int k = 0; k < mat.cols; k++)
                    {
                        os << mat(i, j, k) << " ";
                    }
                    os << std::endl;
                }
                os << std::endl;
            }
            return os;
        }
        inline GArr3D<T> gpu() { return GArr3D<T>(*this); }
        inline const T *begin() const { return data.begin(); }
        inline T *begin() { return data.begin(); }
};

}  // namespace GNNBEM