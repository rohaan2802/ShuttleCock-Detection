# Original submission and data audit

The maintained main uses GitHub commit 280de12. Its tracked tree matched the supplied deployed checkout byte for byte. The previous checkout tip b1b21bb is retained on the local archive/deployed-checkout branch. GitHub Pages serves docs/ at the existing detector URL.

- The [previous deployed README](deployed_readme.md) records the older browser, desktop and deployment workflows.
- [Original variants](original/) contain the older notebook, desktop script, detection log, training arguments epoch results, and the earlier simulation runner. The active browser, training notebook and desktop runner come from the deployed checkout. The two checkpoints named best matched the canonical desktop checkpoint by SHA-256. The distinct last checkpoint is retained for training provenance.
- [Original simulation AVI](media/simulation_original.avi) is preserved for the submission. The existing compressed MP4 is used for the browser and example runner. Historical detector screenshots from the previous site remain under docs/screenshots because they document older interface states. The new gallery uses actual inference, code and evaluation artifacts.
- Reports, course materials, videos, saved predictions, checkpoints and validation plots supplied in the original folder are represented in the checkout. The source folder itself was kept available.

## Dataset

The Desktop release folder contains two parts of the original YOLO ZIP. Upload both files as release assets.

| Release asset | Bytes |
| --- | ---: |
| `ShuttleCock_YOLO_Dataset.zip.part01` | 1,500,000,000 |
| `ShuttleCock_YOLO_Dataset.zip.part02` | 654,446,268 |

Download both parts into the same folder. Reassemble the ZIP outside Git with [join_dataset.py](../scripts/join_dataset.py). The script verifies the original SHA-256 before reporting success.

```powershell
python scripts/join_dataset.py ../ShuttleCock-Detection_Release ../ShuttleCock_YOLO_Dataset.zip
```

The reconstructed ZIP is 2,154,446,268 bytes with SHA-256 `ebe15d48d331ff76ad2b6aae1415a01cd5423fbebee997eada765e44060718ef`. It contains 14,991 JPEGs, 14,991 YOLO labels and one YAML. Keep both release parts together to preserve the complete archive.

| Split | Images |
| --- | ---: |
| Train | 10,816 |
| Validation | 2,666 |
| Test | 1,509 |

The saved YAML refers to a Kaggle input directory. To extract and generate a local config, run:

```powershell
python scripts/prepare_dataset.py ../ShuttleCock_YOLO_Dataset.zip .test-output/dataset
```

Use the resulting `data_local.yaml` with Ultralytics. The original source is documented in the [dataset notes](../My%20Drive/ShuttleBot/datasets/DataSet%20Link.txt). The ZIP is needed for full evaluation or retraining. The browser and desktop detector use the saved model.
