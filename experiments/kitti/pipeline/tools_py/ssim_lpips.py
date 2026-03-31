# scripts/metrics/psnr_ssim_lpips.py
# pip install numpy scikit-image torch lpips pillow
import numpy as np, torch, lpips, argparse, os
from PIL import Image
from skimage.metrics import peak_signal_noise_ratio, structural_similarity

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
TOOLS_DIR = os.path.dirname(SCRIPT_DIR)
OUTPUT_DIR = os.path.join(TOOLS_DIR, 'output')

def to_np_rgb(p): return np.array(Image.open(p).convert('RGB'))

def psnr_ssim(gt_p, out_p):
    gt, out = to_np_rgb(gt_p), to_np_rgb(out_p)
    psnr = peak_signal_noise_ratio(gt, out, data_range=255)
    ssim = structural_similarity(gt, out, channel_axis=2, data_range=255)
    return psnr, ssim

def lpips_v(gt_p, out_p, net='vgg'):
    loss_fn = lpips.LPIPS(net=net)
    def norm(x):
        t = torch.from_numpy(np.array(Image.open(x).convert('RGB'))).permute(2,0,1).unsqueeze(0).float()/255.
        return t*2-1
    with torch.no_grad():
        d = loss_fn(norm(gt_p), norm(out_p)).item()
    return d

def load_cache(cache_path):
    cache = {}
    if os.path.exists(cache_path):
        with open(cache_path, 'r', encoding='utf-8') as f:
            for line in f:
                parts = line.strip().split()
                if len(parts) == 4:
                    fname, p, s, l = parts[0], float(parts[1]), float(parts[2]), float(parts[3])
                    cache[fname] = (p, s, l)
    return cache


def _mean2(a, b):
    return (a + b) / 2.0

if __name__=='__main__':
    ap=argparse.ArgumentParser()
    ap.add_argument('--gt_dir', required=True)
    ap.add_argument('--gt_dir2', default=None)
    ap.add_argument('--enh_dir', required=True)
    args=ap.parse_args()

    norm_path = os.path.normpath(args.enh_dir)
    parts = norm_path.split(os.sep)
    parts = [p for p in parts if p]
    n = parts[-3]

    cache_file = os.path.join(OUTPUT_DIR, "kitti_ssim_lpips_results_" + n + ".txt")
    cache = load_cache(cache_file) if not args.gt_dir2 else {}  # ← 新增：加载缓存

    files=[f for f in os.listdir(args.gt_dir) if f.lower().endswith(('.png','.jpg'))]
    psnrs=[]; ssims=[]; lpips_l=[]
    for f in files:
        print(f)
        if f in cache:
            # ← 新增：从缓存读取
            p, s, l = cache[f]
        else:
            gt_p=os.path.join(args.gt_dir,f); en_p=os.path.join(args.enh_dir,f)
            if args.gt_dir2:
                gt2_p = os.path.join(args.gt_dir2, f)
                p1, s1 = psnr_ssim(gt_p, en_p)
                l1 = lpips_v(gt_p, en_p)
                p2, s2 = psnr_ssim(gt2_p, en_p)
                l2 = lpips_v(gt2_p, en_p)
                p = _mean2(p1, p2)
                s = _mean2(s1, s2)
                l = _mean2(l1, l2)
            else:
                p,s=psnr_ssim(gt_p,en_p); l=lpips_v(gt_p,en_p)
                with open(cache_file, "a", encoding="utf-8") as fout:
                    fout.write(f"{f} {p} {s} {l}\n")

        psnrs.append(p); ssims.append(s); lpips_l.append(l)
    import numpy as np
    print(f'PSNR {np.mean(psnrs):.2f}±{1.96*np.std(psnrs)/np.sqrt(len(psnrs)):.2f}')
    print(f'SSIM {np.mean(ssims):.4f}±{1.96*np.std(ssims)/np.sqrt(len(ssims)):.4f}')
    print(f'LPIPS {np.mean(lpips_l):.4f}±{1.96*np.std(lpips_l)/np.sqrt(len(lpips_l)):.4f}')
    with open(os.path.join(OUTPUT_DIR, "kitti_ssim_lpips_results.txt"), "a", encoding="utf-8") as fout:
        fout.write(n)
        fout.write(f'PSNR {np.mean(psnrs):.2f}±{1.96*np.std(psnrs)/np.sqrt(len(psnrs)):.2f}')
        fout.write(f'SSIM {np.mean(ssims):.4f}±{1.96*np.std(ssims)/np.sqrt(len(ssims)):.4f}')
        fout.write(f'LPIPS {np.mean(lpips_l):.4f}±{1.96*np.std(lpips_l)/np.sqrt(len(lpips_l)):.4f}')
        fout.write('\n')