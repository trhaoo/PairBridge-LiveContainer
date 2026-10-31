// Native iOS 16 command-line host for jailbroken iPhone 8.
// Genuine StikPair Rust engine. Pairing keys and PINs are never fabricated.
#import <Foundation/Foundation.h>
#import <dispatch/dispatch.h>
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include "stikpair.h"

@interface PairAdvertiser : NSObject <NSNetServiceDelegate>
@property(nonatomic,strong) NSNetService *service;
@end
@implementation PairAdvertiser
- (void)netServiceDidPublish:(NSNetService *)sender {
    printf("[Bonjour] PUBLISHED %s port=%ld\n", sender.name.UTF8String, (long)sender.port);
    fflush(stdout);
}
- (void)netService:(NSNetService *)sender didNotPublish:(NSDictionary<NSString *,NSNumber *> *)errors {
    fprintf(stderr, "[Bonjour] PUBLISH FAILED: %s\n", errors.description.UTF8String);
    fflush(stderr);
}
@end

static PairAdvertiser *gAdvertiser;

static void ready_callback(void *ctx, const char *service_id, uint16_t port,
                           const char *const *keys, const char *const *vals, size_t count) {
    @autoreleasepool {
        if (!service_id) return;
        NSString *name = [NSString stringWithUTF8String:service_id];
        NSMutableDictionary<NSString *,NSData *> *txt = [NSMutableDictionary dictionary];
        for (size_t i=0; i<count; i++) {
            if (!keys || !vals || !keys[i] || !vals[i]) continue;
            NSString *key = [NSString stringWithUTF8String:keys[i]];
            NSData *value = [[NSString stringWithUTF8String:vals[i]]
                dataUsingEncoding:NSUTF8StringEncoding];
            if (key && value) txt[key] = value;
        }
        NSDictionary *records = [txt copy];
        printf("[Rust] TCP READY port=%u; TXT records=%zu\n", port, count);
        fflush(stdout);
        dispatch_async(dispatch_get_main_queue(), ^{
            NSNetService *service = [[NSNetService alloc]
                initWithDomain:@"local."
                type:@"_remotepairing-pairable-host._tcp."
                name:name port:(int)port];
            gAdvertiser.service = service;
            service.delegate = gAdvertiser;
            [service setTXTRecordData:[NSNetService dataFromTXTRecordDictionary:records]];
            [service publish];
            printf("[Bonjour] publish requested; check Developer Mode on the iOS 27 iPhone\n");
            fflush(stdout);
        });
    }
}

static void pin_callback(const char *pin, void *ctx) {
    if (!pin) return;
    printf("\n====================================\n");
    printf("   GENUINE REMOTE PAIRING PIN: %s\n", pin);
    printf("====================================\n\n");
    fflush(stdout);
}

int main(int argc, char **argv) {
    @autoreleasepool {
        setvbuf(stdout, NULL, _IONBF, 0);
        setvbuf(stderr, NULL, _IONBF, 0);
        gAdvertiser = [PairAdvertiser new];

        NSString *cwd = [[NSFileManager defaultManager] currentDirectoryPath];
        NSString *path = [cwd stringByAppendingPathComponent:@"rp_pairing_file.plist"];
        printf("StikPairHost-iPhone8 for iOS 16 jailbreak\n");
        printf("Pairing file destination: %s\n", path.UTF8String);
        printf("Keep NewTerm open and both iPhones on the same Wi-Fi.\n");

        dispatch_async(dispatch_get_global_queue(QOS_CLASS_USER_INITIATED, 0), ^{
            StikPairResult r = {0};
            int rc = stikpair_run_host("0.0.0.0", 0, "StikPair-iPhone8", "Mac17,7",
                                      path.UTF8String, ready_callback, pin_callback, NULL, &r);
            printf("[Rust] pairing exited with code=%d\n", rc);
            if (rc == 0) {
                printf("[SUCCESS] Device: %s | UDID: %s\n",
                       r.device_name ? r.device_name : "?",
                       r.device_udid ? r.device_udid : "?");
                printf("[SUCCESS] Private file: %s\n",
                       r.pairing_file_path ? r.pairing_file_path : path.UTF8String);
            } else {
                fprintf(stderr, "[ERROR] %s\n", r.error ? r.error : "unknown");
            }
            stikpair_result_free(&r);
            dispatch_async(dispatch_get_main_queue(), ^{
                [gAdvertiser.service stop];
                exit(rc == 0 ? 0 : 1);
            });
        });
        [[NSRunLoop mainRunLoop] run];
        return 0;
    }
}
