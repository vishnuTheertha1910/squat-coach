# Evaluation status and protocol

**Expert-labeled analysis accuracy: N/A — not evaluated.** Software tests, upstream agreement and visually functioning skeletons do not establish form accuracy. A rule score of 100 is not 100% accuracy.

Freeze the app version, mode and thresholds before collecting final results. A practical pilot could use 10–15 participants and 100–150 repetitions; this is a proposed starting point, not a power calculation or proof of adequate sample size. Use independent recordings under the intended side-view, full-body conditions, with acceptable and faulty repetitions. Avoid counting duplicate clips as independent samples.

Two qualified reviewers should independently label the original recordings, blinded to app predictions, using a written rubric: rep start/bottom/end; acceptable/unacceptable/cannot assess; each supported fault present/absent/cannot assess; visibility and recording problems. Retain initial annotations, measure reviewer agreement, and adjudicate disagreements. Reference labels must not simply repeat the app's thresholds.

Predefine one-to-one rep matching and timing tolerance. Report missed and extra reps, including failed processing and unassessable recordings. Report detection precision/recall/F1, count MAE per video, timestamp error, classification accuracy/balanced accuracy/confusion matrix on matched assessable reps, per-fault precision/recall/F1/support, and assessable coverage. Include participant-based uncertainty intervals and majority-class comparisons. If thresholds are adjusted after inspecting results, evaluate on separate participants.

Manual 2D landmark annotation can provide a reference for image-based thigh inclination. 3D coordinate accuracy requires an appropriate calibrated reference, such as motion capture; expert video labels alone do not validate it. See [scikit-learn's metric definitions](https://scikit-learn.org/stable/modules/model_evaluation.html).

No expert labels or benchmark scores are invented in this repository. The archived results preserve the app's predictions, not ground truth.
