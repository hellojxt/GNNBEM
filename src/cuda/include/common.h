#pragma once
#include <array>
#include <cstdint>
#include <iostream>
#include <sstream>
#include <stdexcept>
#include <string>
#include <curand_kernel.h>
#include <thrust/complex.h>
#include "helper_math.h"
#include <random>

#define NWOB_NAMESPACE_BEGIN \
    namespace nwob           \
    {
#define NWOB_NAMESPACE_END }

NWOB_NAMESPACE_BEGIN

using complex = thrust::complex<float>;
using randomState = curandState_t;
#define RAND_F (float)rand() / (float)RAND_MAX
#define STRINGIFY(x) #x
#define STR(x) STRINGIFY(x)
#define FILE_LINE __FILE__ ":" STR(__LINE__)

/// Checks the result of a cuXXXXXX call and throws an error on failure
#define CU_CHECK_THROW(x)                                                                        \
    do                                                                                           \
    {                                                                                            \
        CUresult result = x;                                                                     \
        if (result != CUDA_SUCCESS)                                                              \
        {                                                                                        \
            const char *msg;                                                                     \
            cuGetErrorName(result, &msg);                                                        \
            throw std::runtime_error(std::string(FILE_LINE " " #x " failed with error ") + msg); \
        }                                                                                        \
    } while (0)

/// Checks the result of a cuXXXXXX call and prints an error on failure
#define CU_CHECK_PRINT(x)                                                            \
    do                                                                               \
    {                                                                                \
        CUresult result = x;                                                         \
        if (result != CUDA_SUCCESS)                                                  \
        {                                                                            \
            const char *msg;                                                         \
            cuGetErrorName(result, &msg);                                            \
            std::cout << FILE_LINE " " #x " failed with error " << msg << std::endl; \
        }                                                                            \
    } while (0)

/// Checks the result of a cudaXXXXXX call and throws an error on failure
#define CUDA_CHECK_THROW(x)                                                                \
    do                                                                                     \
    {                                                                                      \
        cudaError_t result = x;                                                            \
        if (result != cudaSuccess)                                                         \
            throw std::runtime_error(std::string(FILE_LINE " " #x " failed with error ") + \
                                     cudaGetErrorString(result));                          \
    } while (0)

/// Checks the result of a cudaXXXXXX call and prints an error on failure
#define CUDA_CHECK_PRINT(x)                                                                                 \
    do                                                                                                      \
    {                                                                                                       \
        cudaError_t result = x;                                                                             \
        if (result != cudaSuccess)                                                                          \
            std::cout << FILE_LINE " " #x " failed with error " << cudaGetErrorString(result) << std::endl; \
    } while (0)

#define HOST_DEVICE __host__ __device__
constexpr uint32_t n_threads_linear = 128;

template <typename T>
HOST_DEVICE T div_round_up(T val, T divisor)
{
    return (val + divisor - 1) / divisor;
}

template <typename T>
constexpr uint32_t n_blocks_linear(T n_elements)
{
    return (uint32_t)div_round_up(n_elements, (T)n_threads_linear);
}

template <typename K, typename T, typename... Types>
inline void linear_kernel(K kernel, T n_elements, Types... args)
{
    if (n_elements <= 0)
    {
        return;
    }
    kernel<<<n_blocks_linear(n_elements), n_threads_linear>>>(args...);
}

template <typename F>
__global__ void parallel_for_kernel(const size_t n_elements, F fun)
{
    const size_t i = threadIdx.x + blockIdx.x * blockDim.x;
    if (i >= n_elements)
        return;
    fun(i);
}

template <typename F>
inline void parallel_for(uint32_t shmem_size, size_t n_elements, F &&fun)
{
    if (n_elements <= 0)
    {
        return;
    }
    parallel_for_kernel<F><<<n_blocks_linear(n_elements), n_threads_linear, shmem_size>>>(n_elements, fun);
}

template <typename F>
inline void parallel_for(size_t n_elements, F &&fun)
{
    parallel_for(0, n_elements, std::forward<F>(fun));
}

template <typename F>
__global__ void parallel_for_aos_kernel(const size_t n_elements, const uint32_t n_dims, F fun)
{
    const size_t dim = threadIdx.x;
    const size_t elem = threadIdx.y + blockIdx.x * blockDim.y;
    if (dim >= n_dims)
        return;
    if (elem >= n_elements)
        return;

    fun(elem, dim);
}

template <typename F>
inline void parallel_for_aos(uint32_t shmem_size, size_t n_elements, uint32_t n_dims, F &&fun)
{
    if (n_elements <= 0 || n_dims <= 0)
    {
        return;
    }
    const dim3 threads = {n_dims, div_round_up(n_threads_linear, n_dims), 1};
    const size_t n_threads = threads.x * threads.y;
    const dim3 blocks = {(uint32_t)div_round_up(n_elements * n_dims, n_threads), 1, 1};

    parallel_for_aos_kernel<<<blocks, threads, shmem_size>>>(n_elements, n_dims, fun);
}

template <typename F>
inline void parallel_for_aos(size_t n_elements, uint32_t n_dims, F &&fun)
{
    parallel_for_aos(0, n_elements, n_dims, std::forward<F>(fun));
}

template <typename F>
__global__ void parallel_for_soa_kernel(const size_t n_elements, const uint32_t n_dims, F fun)
{
    const size_t elem = threadIdx.x + blockIdx.x * blockDim.x;
    const size_t dim = blockIdx.y;
    if (elem >= n_elements)
        return;
    if (dim >= n_dims)
        return;

    fun(elem, dim);
}

template <typename F>
inline void parallel_for_soa(uint32_t shmem_size, size_t n_elements, uint32_t n_dims, F &&fun)
{
    if (n_elements <= 0 || n_dims <= 0)
    {
        return;
    }

    const dim3 blocks = {n_blocks_linear(n_elements), n_dims, 1};
    parallel_for_soa_kernel<<<n_blocks_linear(n_elements), n_threads_linear, shmem_size>>>(n_elements, n_dims, fun);
}

template <typename F>
inline void parallel_for_soa(size_t n_elements, uint32_t n_dims, F &&fun)
{
    parallel_for_soa(0, n_elements, n_dims, std::forward<F>(fun));
}

/*
    Neumann boundary equation:

    u(x) = 2∫ ∂G u - 2∫ G ∂u

    where G is the Green's function of the Laplacian operator, and ∂G is the normal derivative of G.
*/

enum
{
    POSSION = 0,
    HELMHOLTZ = 1,
};

template <int type>
HOST_DEVICE inline complex Green_func(float3 y, float3 x, float k);

template <int type>
HOST_DEVICE inline complex Green_func_deriv(float3 y, float3 x, float3 xn, float k);

template <>
HOST_DEVICE inline complex Green_func<HELMHOLTZ>(float3 y, float3 x, float k)
{
    float r = length(x - y);
    if (r < 1e-6)
        return complex(0, 0);
    return exp(complex(0, k * r)) / (4 * M_PI * r);
}

template <>
HOST_DEVICE inline complex Green_func_deriv<HELMHOLTZ>(float3 y, float3 x, float3 xn, float k)
{
    float r = length(x - y);
    if (r < 1e-6)
        return complex(0, 0);
    complex ikr = complex(0, 1) * r * k;
    complex potential = -exp(ikr) / (4 * M_PI * r * r * r) * (1 - ikr) * dot(x - y, xn);
    return potential;
}

template <>
HOST_DEVICE inline complex Green_func<POSSION>(float3 y, float3 x, float k)
{
    float r = length(x - y);
    return 1 / (4 * M_PI * r);
}

template <>
HOST_DEVICE inline complex Green_func_deriv<POSSION>(float3 y, float3 x, float3 xn, float k)
{
    float r = length(x - y);
    return -1 / (4 * M_PI * r * r * r) * dot(x - y, xn);
}

inline std::vector<unsigned long long> get_random_seeds(int n)
{
    std::mt19937_64 random(0);  // fixed seed (for debugging)
    std::vector<unsigned long long> seeds(n);
    for (auto &seed : seeds)
        seed = random();
    return seeds;
}

NWOB_NAMESPACE_END