# Historical prototype provenance

`legacy/original` contains byte-for-byte snapshots of every file that existed
before the maintained non-diagnostic sandbox was added. The same original bytes
also remain at their existing repository paths for link and history stability.

| Original path | First repository commit | Commit timestamp |
|---|---|---|
| `README.md` | `47b3afc7df3e8a2a38af13ecf339576d6fb31656` | `2025-09-27T12:50:06-07:00` |
| `backend/app.py` | `b1b4589ad614e43b47b0a8882dbfe34db62dc600` | `2025-09-27T12:47:07-07:00` |
| `frontend/app.js` | `a740b68d69fb87bf1a80e40eeae24a030fb02519` | `2025-09-27T12:42:01-07:00` |
| `frontend/index.html` | `75651d8e788cf9c88b63d4482baddedac01d7794` | `2025-09-27T12:41:15-07:00` |
| `frontend/public/index.html` | `7836694cdb8c2bec32339c45d5dc58966b42c59b` | `2025-09-27T12:46:31-07:00` |
| `frontend/src/App.css` | `fbe62dc43134d455ee494a001327cdcb879ca41b` | `2025-09-27T12:45:47-07:00` |
| `frontend/src/App.js` | `aff2317f87f22dadd546f947ccd7796eec0d024c` | `2025-09-27T12:45:08-07:00` |
| `frontend/styles.css` | `67654a9b1fc6aa52f39b592a27ca716f481074db` | `2025-09-27T12:41:36-07:00` |
| `model/predict.py` | `20c4cb8879eb7e77af4e7245af92b5d6f5abcadc` | `2025-09-27T12:44:36-07:00` |
| `model/preprocess.py` | `adc808ebc06a96e7af33a9a066d961f23f8e3717` | `2025-09-27T12:42:55-07:00` |
| `model/training.py` | `20b3f8e0d5ec476d00ac5315ccf311408c083663` | `2025-09-27T12:43:26-07:00` |

The historical files include unsafe labels, random mock output, shared upload
paths, unresolved imports, and a debug entry point. They are not imported,
packaged, served, or copied into the production container. Use
`acoustic_sandbox` and the root `README.md` for all maintained workflows.
