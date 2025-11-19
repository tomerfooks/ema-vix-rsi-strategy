#ifdef __APPLE__
#include <OpenCL/opencl.h>
#else
#include <CL/cl.h>
#endif

#include <stdio.h>

int main() {
    cl_uint num_platforms;
    clGetPlatformIDs(0, NULL, &num_platforms);
    
    printf("Found %d OpenCL platform(s)\n\n", num_platforms);
    
    cl_platform_id* platforms = malloc(num_platforms * sizeof(cl_platform_id));
    clGetPlatformIDs(num_platforms, platforms, NULL);
    
    for (int i = 0; i < num_platforms; i++) {
        char name[128];
        clGetPlatformInfo(platforms[i], CL_PLATFORM_NAME, sizeof(name), name, NULL);
        printf("Platform %d: %s\n", i, name);
        
        cl_uint num_devices;
        clGetDeviceIDs(platforms[i], CL_DEVICE_TYPE_ALL, 0, NULL, &num_devices);
        
        cl_device_id* devices = malloc(num_devices * sizeof(cl_device_id));
        clGetDeviceIDs(platforms[i], CL_DEVICE_TYPE_ALL, num_devices, devices, NULL);
        
        for (int j = 0; j < num_devices; j++) {
            char device_name[128];
            cl_device_type device_type;
            cl_uint compute_units;
            cl_ulong global_mem;
            
            clGetDeviceInfo(devices[j], CL_DEVICE_NAME, sizeof(device_name), device_name, NULL);
            clGetDeviceInfo(devices[j], CL_DEVICE_TYPE, sizeof(device_type), &device_type, NULL);
            clGetDeviceInfo(devices[j], CL_DEVICE_MAX_COMPUTE_UNITS, sizeof(compute_units), &compute_units, NULL);
            clGetDeviceInfo(devices[j], CL_DEVICE_GLOBAL_MEM_SIZE, sizeof(global_mem), &global_mem, NULL);
            
            printf("  Device %d: %s\n", j, device_name);
            printf("    Type: ");
            if (device_type & CL_DEVICE_TYPE_GPU) printf("GPU ");
            if (device_type & CL_DEVICE_TYPE_CPU) printf("CPU ");
            printf("\n");
            printf("    Compute Units: %u\n", compute_units);
            printf("    Memory: %.2f GB\n\n", global_mem / 1e9);
        }
        
        free(devices);
    }
    
    free(platforms);
    return 0;
}
