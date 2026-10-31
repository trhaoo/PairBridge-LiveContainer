// StikPair Bridge iOS 16: native UIKit shell around the genuine StikPair Rust RemotePairing engine.
// Run on a secondary iPhone 8, with the iOS 27 iPhone selecting the advertised host in Settings.
#import <UIKit/UIKit.h>
#import <Foundation/Foundation.h>
#import <dispatch/dispatch.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>
#include "stikpair.h"

@interface PairViewController : UIViewController <NSNetServiceDelegate>
@property(nonatomic,strong) UILabel *statusLabel;
@property(nonatomic,strong) UILabel *pinLabel;
@property(nonatomic,strong) UITextView *logView;
@property(nonatomic,strong) UIButton *pairButton;
@property(nonatomic,strong) UIButton *shareButton;
@property(nonatomic,strong) NSNetService *service;
@property(nonatomic,strong) NSURL *pairingURL;
@property(nonatomic,assign) BOOL pairing;
@property(nonatomic,assign) NSUInteger runNumber;
- (void)beginPairing;
- (void)onReady:(const char *)identifier port:(uint16_t)port keys:(const char *const *)keys values:(const char *const *)values count:(size_t)count;
- (void)onPIN:(const char *)pin;
- (void)onFinish:(int)code result:(StikPairResult *)result;
- (void)logMessage:(NSString *)message;
@end

static void callbackReady(void *context, const char *identifier, uint16_t port,
                          const char *const *keys, const char *const *values, size_t count) {
    PairViewController *vc = (__bridge PairViewController *)context;
    [vc onReady:identifier port:port keys:keys values:values count:count];
}
static void callbackPIN(const char *pin, void *context) {
    PairViewController *vc = (__bridge PairViewController *)context;
    [vc onPIN:pin];
}

@implementation PairViewController
- (UILabel *)makeLabel:(CGFloat)size weight:(UIFontWeight)weight color:(UIColor *)color {
    UILabel *label = [[UILabel alloc] init];
    label.font = [UIFont systemFontOfSize:size weight:weight];
    label.textColor = color;
    label.numberOfLines = 0;
    label.textAlignment = NSTextAlignmentCenter;
    label.translatesAutoresizingMaskIntoConstraints = NO;
    return label;
}
- (UIButton *)makeButton:(NSString *)title color:(UIColor *)color {
    UIButton *button = [UIButton buttonWithType:UIButtonTypeSystem];
    button.translatesAutoresizingMaskIntoConstraints = NO;
    button.backgroundColor = color;
    button.layer.cornerRadius = 13;
    button.clipsToBounds = YES;
    [button setTitle:title forState:UIControlStateNormal];
    [button setTitleColor:UIColor.whiteColor forState:UIControlStateNormal];
    button.titleLabel.font = [UIFont systemFontOfSize:16 weight:UIFontWeightSemibold];
    return button;
}
- (void)viewDidLoad {
    [super viewDidLoad];
    self.view.backgroundColor = [UIColor colorWithRed:0.065 green:0.078 blue:0.128 alpha:1];
    [UIApplication sharedApplication].idleTimerDisabled = NO;

    UIColor *white = UIColor.whiteColor;
    UIColor *muted = [UIColor colorWithRed:0.72 green:0.77 blue:0.88 alpha:1];
    UILabel *title = [self makeLabel:26 weight:UIFontWeightBold color:white];
    title.text = @"StikPair Bridge";
    UILabel *subtitle = [self makeLabel:13 weight:UIFontWeightRegular color:muted];
    subtitle.text = @"iPhone 8 · iOS 16+\nMáy chủ ghép đôi cho iPhone chính";
    self.statusLabel = [self makeLabel:15 weight:UIFontWeightMedium color:muted];
    self.statusLabel.text = @"Sẵn sàng";
    self.pinLabel = [self makeLabel:30 weight:UIFontWeightBold color:[UIColor colorWithRed:0.38 green:0.91 blue:0.79 alpha:1]];
    self.pinLabel.text = @"PIN: —";
    self.pinLabel.accessibilityLabel = @"Mã PIN ghép đôi";
    self.pairButton = [self makeButton:@"Bắt đầu ghép đôi" color:[UIColor colorWithRed:0.13 green:0.40 blue:0.94 alpha:1]];
    [self.pairButton addTarget:self action:@selector(beginPairing) forControlEvents:UIControlEventTouchUpInside];
    self.shareButton = [self makeButton:@"Xuất file PR" color:[UIColor colorWithRed:0.21 green:0.28 blue:0.38 alpha:1]];
    [self.shareButton addTarget:self action:@selector(sharePairing) forControlEvents:UIControlEventTouchUpInside];
    self.shareButton.enabled = NO;
    self.shareButton.alpha = 0.45;
    UILabel *guide = [self makeLabel:12 weight:UIFontWeightRegular color:muted];
    guide.text = @"Giữ ứng dụng này mở và cả hai iPhone cùng Wi-Fi.\nTrên iPhone chính: Developer Mode → Pair with StikPair.";
    UILabel *logTitle = [self makeLabel:13 weight:UIFontWeightSemibold color:muted];
    logTitle.text = @"Nhật ký kết nối";
    logTitle.textAlignment = NSTextAlignmentLeft;
    self.logView = [[UITextView alloc] init];
    self.logView.backgroundColor = [UIColor colorWithRed:0.11 green:0.15 blue:0.22 alpha:1];
    self.logView.layer.cornerRadius = 10;
    self.logView.textColor = UIColor.whiteColor;
    self.logView.font = [UIFont monospacedSystemFontOfSize:11 weight:UIFontWeightRegular];
    self.logView.editable = NO;
    self.logView.selectable = YES;
    self.logView.textContainerInset = UIEdgeInsetsMake(10,9,10,9);
    self.logView.translatesAutoresizingMaskIntoConstraints = NO;
    self.logView.text = @"Chưa bắt đầu.\n";

    UIStackView *stack = [[UIStackView alloc] initWithArrangedSubviews:
        @[title,subtitle,self.statusLabel,self.pinLabel,self.pairButton,self.shareButton,guide,logTitle,self.logView]];
    stack.axis = UILayoutConstraintAxisVertical;
    stack.spacing = 11;
    stack.translatesAutoresizingMaskIntoConstraints = NO;
    [self.view addSubview:stack];

    [NSLayoutConstraint activateConstraints:@[
        [stack.leadingAnchor constraintEqualToAnchor:self.view.safeAreaLayoutGuide.leadingAnchor constant:18],
        [stack.trailingAnchor constraintEqualToAnchor:self.view.safeAreaLayoutGuide.trailingAnchor constant:-18],
        [stack.topAnchor constraintEqualToAnchor:self.view.safeAreaLayoutGuide.topAnchor constant:17],
        [stack.bottomAnchor constraintLessThanOrEqualToAnchor:self.view.safeAreaLayoutGuide.bottomAnchor constant:-12],
        [self.pairButton.heightAnchor constraintEqualToConstant:47],
        [self.shareButton.heightAnchor constraintEqualToConstant:47],
        [self.pinLabel.heightAnchor constraintGreaterThanOrEqualToConstant:47],
        [self.logView.heightAnchor constraintGreaterThanOrEqualToConstant:150]
    ]];
    [self logMessage:@"Ứng dụng UIKit iOS 16 đã khởi động."];
}
- (void)logMessage:(NSString *)message {
    if (!message) return;
    if (![NSThread isMainThread]) {
        dispatch_async(dispatch_get_main_queue(), ^{ [self logMessage:message]; });
        return;
    }
    NSDateFormatter *df = [[NSDateFormatter alloc] init];
    df.dateFormat = @"HH:mm:ss";
    NSString *line = [NSString stringWithFormat:@"[%@] %@\n", [df stringFromDate:NSDate.date], message];
    NSString *existing = self.logView.text ?: @"";
    if (existing.length > 14000) existing = [existing substringFromIndex:(existing.length - 9000)];
    self.logView.text = [existing stringByAppendingString:line];
    [self.logView scrollRangeToVisible:NSMakeRange(self.logView.text.length, 0)];
}
- (void)beginPairing {
    if (self.pairing) return;
    self.pairing = YES;
    self.runNumber += 1;
    self.pinLabel.text = @"PIN: —";
    self.statusLabel.text = @"Đang chờ iPhone chính kết nối...";
    self.pairButton.enabled = NO;
    self.pairButton.alpha = 0.5;
    self.shareButton.enabled = NO;
    self.shareButton.alpha = 0.45;
    self.service.delegate = nil;
    [self.service stop];
    self.service = nil;
    [UIApplication sharedApplication].idleTimerDisabled = YES;

    NSString *documents = NSSearchPathForDirectoriesInDomains(NSDocumentDirectory, NSUserDomainMask, YES).firstObject;
    self.pairingURL = [NSURL fileURLWithPath:[documents stringByAppendingPathComponent:@"rp_pairing_file.plist"]];
    [self logMessage:@"Bắt đầu máy chủ RemotePairing (PIN chỉ hiện sau TCP handshake)."];
    const char *outPath = self.pairingURL.path.UTF8String;
    NSString *pathCopy = [NSString stringWithUTF8String:outPath];
    // Keep the controller alive through the C callback sequence.
    void *context = (__bridge_retained void *)self;
    dispatch_async(dispatch_get_global_queue(QOS_CLASS_USER_INITIATED, 0), ^{
        StikPairResult result = {0};
        int code = stikpair_run_host("0.0.0.0", 0, "StikPair-iPhone8", "Mac17,7",
                                     pathCopy.UTF8String, callbackReady, callbackPIN,
                                     context, &result);
        [self onFinish:code result:&result];
        stikpair_result_free(&result);
        CFBridgingRelease(context);
    });
}
- (void)onReady:(const char *)identifier port:(uint16_t)port
           keys:(const char *const *)keys values:(const char *const *)values count:(size_t)count {
    if (!identifier) return;
    if (strcmp(identifier, "__stikpair_tcp_accepted__") == 0) {
        [self logMessage:[NSString stringWithFormat:@"TCP ACCEPTED · cổng %u",port]];
        return;
    }
    NSString *serviceId = [NSString stringWithUTF8String:identifier];
    if (!serviceId) return;
    NSMutableDictionary<NSString *,NSData *> *records = [NSMutableDictionary dictionary];
    for (size_t index = 0; index < count; index++) {
        if (!keys || !values || !keys[index] || !values[index]) continue;
        NSString *key = [NSString stringWithUTF8String:keys[index]];
        NSString *value = [NSString stringWithUTF8String:values[index]];
        if (key && value) records[key] = [value dataUsingEncoding:NSUTF8StringEncoding];
    }
    NSDictionary *copiedRecords = [records copy];
    [self logMessage:[NSString stringWithFormat:@"Rust READY · cổng %u · TXT %zu", port, count]];
    dispatch_async(dispatch_get_main_queue(), ^{
        NSNetService *service = [[NSNetService alloc] initWithDomain:@"local."
            type:@"_remotepairing-pairable-host._tcp." name:serviceId port:(int)port];
        service.delegate = self;
        self.service = service;
        [service setTXTRecordData:[NSNetService dataFromTXTRecordDictionary:copiedRecords]];
        [service publish];
        [self logMessage:@"Bonjour publish() đã được yêu cầu."];
    });
}
- (void)onPIN:(const char *)pin {
    if (!pin) return;
    NSString *code = [NSString stringWithUTF8String:pin];
    dispatch_async(dispatch_get_main_queue(), ^{
        self.pinLabel.text = [@"PIN: " stringByAppendingString:code ?: @""];
        self.statusLabel.text = @"Nhập 6 số này trên iPhone chính";
        [self logMessage:@"Đã nhận PIN thật từ Rust; nhập mã đang hiển thị."];
    });
}
- (void)onFinish:(int)code result:(StikPairResult *)result {
    NSString *error = result->error ? [NSString stringWithUTF8String:result->error] : @"không rõ";
    NSString *device = result->device_name ? [NSString stringWithUTF8String:result->device_name] : @"iPhone";
    dispatch_async(dispatch_get_main_queue(), ^{
        self.pairing = NO;
        self.pairButton.enabled = YES;
        self.pairButton.alpha = 1;
        [UIApplication sharedApplication].idleTimerDisabled = NO;
        self.service.delegate = nil;
        [self.service stop];
        self.service = nil;
        if (code == 0 && [[NSFileManager defaultManager] fileExistsAtPath:self.pairingURL.path]) {
            self.statusLabel.text = [NSString stringWithFormat:@"Ghép đôi thành công: %@",device];
            [self logMessage:@"Đã tạo file PR thật trong Documents."];
            self.shareButton.enabled = YES;
            self.shareButton.alpha = 1;
            [self.pairButton setTitle:@"Ghép đôi thiết bị khác" forState:UIControlStateNormal];
        } else {
            self.statusLabel.text = @"Ghép đôi chưa thành công";
            [self logMessage:[NSString stringWithFormat:@"Rust exit=%d, lỗi: %@",code,error]];
            [self.pairButton setTitle:@"Thử lại" forState:UIControlStateNormal];
        }
    });
}
- (void)netServiceDidPublish:(NSNetService *)sender {
    [self logMessage:[NSString stringWithFormat:@"BONJOUR PUBLISHED · port %ld",(long)sender.port]];
}
- (void)netService:(NSNetService *)sender didNotPublish:(NSDictionary<NSString *,NSNumber *> *)errors {
    [self logMessage:[NSString stringWithFormat:@"BONJOUR FAILED · %@",errors.description]];
}
- (void)sharePairing {
    if (!self.pairingURL || ![[NSFileManager defaultManager] fileExistsAtPath:self.pairingURL.path]) {
        [self logMessage:@"Chưa có file PR hợp lệ để chia sẻ."];
        return;
    }
    UIActivityViewController *share = [[UIActivityViewController alloc]
        initWithActivityItems:@[self.pairingURL] applicationActivities:nil];
    if (share.popoverPresentationController) {
        share.popoverPresentationController.sourceView = self.shareButton;
        share.popoverPresentationController.sourceRect = self.shareButton.bounds;
    }
    [self presentViewController:share animated:YES completion:nil];
}
@end

@interface AppDelegate : UIResponder <UIApplicationDelegate>
@property(nonatomic,strong) UIWindow *window;
@end
@implementation AppDelegate
- (BOOL)application:(UIApplication *)application didFinishLaunchingWithOptions:(NSDictionary *)launchOptions {
    self.window = [[UIWindow alloc] initWithFrame:UIScreen.mainScreen.bounds];
    self.window.rootViewController = [[PairViewController alloc] init];
    [self.window makeKeyAndVisible];
    return YES;
}
@end

int main(int argc, char *argv[]) {
    @autoreleasepool {
        return UIApplicationMain(argc, argv, nil, NSStringFromClass([AppDelegate class]));
    }
}
