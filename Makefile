## Make targets for routine tasks

update:
	@echo "Running multi-chain data extraction..."
	python -m src.extract_multi_chain

reproduce:
	@echo "Regenerating paper figures + stress curves (offline)..."
	python gen_paper_figs.py
	@echo "Exporting LaTeX snippets used by the report..."
	python scripts/export_paper_latex.py

sync-report:
	@echo "Syncing PDF figures into ../template_extracted ..."
	cp -f figs/fig*.pdf ../template_extracted/
