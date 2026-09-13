84 arithmetic diagnostic records; not convolution correctness or benchmark results.
Each mixed step has four FMOPA instructions plus N FMLA instructions on independent accumulators.
Values are medians of three thread-mean timings; cycles use the explicit 1.55 GHz normalization.

| Variant | One thread ns/step | One thread normalized cycles | 38 threads ns/step | 38 threads normalized cycles |
| --- | ---: | ---: | ---: | ---: |
| mix0 | 5.161295 | 8.0000 | 5.161600 | 8.0005 |
| mix2 | 5.161295 | 8.0000 | 5.161521 | 8.0004 |
| mix4 | 5.161295 | 8.0000 | 5.161608 | 8.0005 |
| mix6 | 5.161295 | 8.0000 | 5.161545 | 8.0004 |
| mix8 | 5.161295 | 8.0000 | 5.161633 | 8.0005 |
| mix10 | 6.451618 | 10.0000 | 6.451909 | 10.0005 |
| mix12 | 7.741940 | 12.0000 | 7.742294 | 12.0006 |
| mix16 | 10.322585 | 16.0000 | 10.323174 | 16.0009 |
| mix18 | 11.612908 | 18.0000 | 11.613448 | 18.0008 |
| vec2 | 1.612912 | 2.5000 | 1.613557 | 2.5010 |
| vec4 | 1.886602 | 2.9242 | 1.886684 | 2.9244 |
| vec8 | 2.580650 | 4.0000 | 2.580781 | 4.0002 |
| vec16 | 5.161295 | 8.0000 | 5.161621 | 8.0005 |
| vec18 | 5.806457 | 9.0000 | 5.807073 | 9.0010 |
