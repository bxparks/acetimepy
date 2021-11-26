benchmark.txt:
	python3 benchmark.py > $@

README.md: benchmark.txt generate_readme.py
	./generate_readme.py > $@

clean:
	rm -f benchmark.txt
