# What do other tools show us here?

Open `views/index.html` directly. The collection has 17 exhibits, 21 exhibit/checkpoint combinations and 157 paired replays. The counts include repeated interventions on the same prompt. Each instrument page in the shared submission site also links to its companion cases. The full instrument menu stays visible on every case.

## Three doors in

- **Leg Day, 9B.** One full residual copy at block 15 takes the spider question from 8 to 6 when the donor clue ends in “honey.” The three-example identity Patchscope ranks “ web” and “ honey” first. Its unpatched receiver ranks “ X.” The full Skeleton Lens ranks spider eighth before the copy and bee first afterward. Change the case to the ant donor. The model answers 4 and the full Skeleton Lens puts ant at rank 2,285. The raw lens includes the fragments exactly as returned by the tokenizer.
- **The E6 Incident.** On public OthelloGPT game 527, a white-to-black reflection in the E6 probe direction flips the probe classification. According to the rules, E7 and F7 become legal. Together their probability goes from 0.00085% to 0.00129%. The newly illegal G6 keeps about 8.3%. The clean model puts an average of 99.97% mass on legal moves across the 64 reference boards. This replay uses a public linear probe and one board selected using game rules, so it tests the intervention on one position.
- **Knock on Sky.** Open Original intervention and switch between the upper and lower sites. The same 15-channel door brush makes a small gray mark in the sky and an arched opening in the wall. Inspect GANPaint brush · door to see which individual channels were moved. ACE targets local brightness in this replay. Neither the derivative nor the RGB difference is a door classifier.

## What was measured

The Rome rank-one weight write puts Rome first on both held-out fictional-guide prompts. It also changes the top completion of “The capital of France is” from Paris to Rome. The cold and arithmetic controls retain their top answers.

The 15 Qwen3.5-9B language exhibits use frozen source/donor prompts, zero-based positions, checkpoint revision and intervention. Legs, Brass, Pause and Rabbit use the zoo’s own tasks. The other eleven are **new prompt-pair analogues**. Their full-state transplants are independent experiments. The literature interventions linked from the exhibit pages retain their original model and site.

Additional runs use Qwen3.5-4B on Legs, Brass and Rabbit, the Llama 3.1 8B base article community, the synthetic OthelloGPT checkpoint and the LSUN church generator. The article sweep has 16 stems × four interventions on each of two checkpoints. For 9B its residual read at block 27 is partway through the six-layer intervention. Native neurons, downstream heads and the six community coordinates each have their own stated hooks.

The 9B vocabulary readers include the unfiltered raw head, three frozen forward-only Skeleton branches, released J, J++, R and J-1000 maps, a locally distilled rank-16 tuned lens, an identity Patchscope and a fixed one-token-ahead receiver. The raw head and locally fitted/receiver readers use original vocabulary order without exclusions. The release and Skeleton rankings share a fixed token exclusion list. The 4B R and J++ maps use the exclusion list from their own release. Token IDs disambiguate visually identical decoded fragments.

ICA and PCA use all reference rows. The mean, ACE and gradient directions use rows labelled 0 or 1. Axis orientation, scale and initial display choice are set on those references. Native features include 64 local top-eight transcoder latents per block. Their held-out explained variance ranges from 3.2% to 12.2%. The small learned two-question activation reader recovered the exact current or preceding token on only 1–2 of 48 held-out positions, depending on question and layer. Its matched, shuffled-state and question-only controls are available on every 9B case.

The function-vector readout uses four demonstration queries during head selection and reports that selection-set restoration score. The one-hop attribution reads contributions through the small transcoder. The ROME-style readout measures the input-side response of a proposed rank-one writer. A separate Rome weight-edit trial optimizes a left vector and records two rewrite and four retention prompts. These local adaptations have narrower targets than their published counterparts. A missing fit or architectural incompatibility has a selectable entry.

## Replay checks

All four 9B Legs outcomes and all 64 9B article top tokens agree with the earlier runs. The three 9B Brass constrained choices agree in both conditions. The Llama article rerun matches 59 of 64 archived edited top tokens. It used eager attention on MPS in single prompts, while the archive used batched CUDA SDPA. The two 4B Rabbit clean lines and one of the two edited lines match exactly. The other edited line ends in “dead” in the rerun and “sand” in the archive. Each discrepancy is attached to its case and retained in `CHECKS.json`.

## Adding the next animal

1. Register the case, literal receiver and donor, checkpoint revision, edited and read positions, token IDs, layer, hook and condition before displaying a result. For spatial and board models use native cell or move coordinates.
2. Run the whole instrument roster on those two states. Record real coordinates, reference contexts, signed projections, token ranks, receiver controls and actual generated outputs as appropriate. Keep flat and failed trials. Put comparisons that change the model, site, receiver or intervention in their own named case.
3. Keep reference examples and selection rules separate from the replay. Label locally fitted substitutes and show their held-out checks. Log each tool’s own causal edit, strength, outcome and retention test as a separate trial.
4. Run `assemble.py` and `install_site.py PATH_TO_SITE`. The generator validates case IDs, reference dimensions, token positions, attention normalization and paired rank lists. Every instrument gets either a measurement, a named adaptation, or a reason the cell is open. The case, tool and coordinate are shareable in the URL fragment.

## Source records and reproduction

`fixtures.json` freezes the literal public language inputs. `selection.json` fixes the article members and random control. `records/` holds primary runs, while `extra/`, `routes/`, `oracle/` and `writer/` hold additional readings joined by case ID. `views/data/` contains the complete joined rows used by the browser. The source scripts, saved local fits, release pins and baseline comparisons accompany the collection.

The 9B sequence is `fit_features.py`, `run-a40.sh`, `supplement.py`, `routes.py`, `oracle.py`, `writer.py` and `run-a40.sh --poem-next`. The A40 environment paths are in the launcher. The independent prose corpus is the Skeleton fit’s public `fit_prompts.json`. `small.py` runs the smaller Qwen fits and `small.py --llama` uses the archived Llama selection. The gallery’s native church code uses the GANPaint demo port at c35b3978 and its church weights at b9743a30. Public Othello code, games and probe are from f23bb569 and weights are from 905ca1a6. The game bank is disjoint from our statistical fit by game ID. The public board probe was trained separately and may have seen the showcased board.

[GAN Dissection](https://github.com/CSAILVision/gandissect) · [GANPaint port](https://github.com/hendrikstrobelt/ganpaint_2026) · [Church weights and brushes](https://huggingface.co/hen/ganpaint-churchoutdoor) · [Othello games and probe](https://github.com/likenneth/othello_world) · [OthelloGPT weights](https://huggingface.co/NeelNanda/Othello-GPT-Transformer-Lens)
