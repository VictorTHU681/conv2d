84 arithmetic diagnostic records; not convolution correctness or benchmark results.
Each mixed step has four FMOPA instructions plus N FMLA instructions on independent accumulators.
Values are medians of three thread-mean timings; cycles use the explicit 1.55 GHz normalization.

| Variant | One thread ns/step | One thread normalized cycles | 38 threads ns/step | 38 threads normalized cycles |
| --- | ---: | ---: | ---: | ---: |
| mix0 | 5.161295 | 8.0000 | 5.162253 | 8.0015 |
| mix2 | 5.161295 | 8.0000 | 5.161490 | 8.0003 |
| mix4 | 5.161295 | 8.0000 | 5.161942 | 8.0010 |
| mix6 | 5.161295 | 8.0000 | 5.161482 | 8.0003 |
| mix8 | 5.161295 | 8.0000 | 5.161621 | 8.0005 |
| mix10 | 6.451615 | 10.0000 | 6.452056 | 10.0007 |
| mix12 | 7.741940 | 12.0000 | 7.742253 | 12.0005 |
| mix16 | 10.322585 | 16.0000 | 10.323826 | 16.0019 |
| mix18 | 11.612908 | 18.0000 | 11.615608 | 18.0042 |
| vec2 | 1.693555 | 2.6250 | 1.693061 | 2.6242 |
| vec4 | 1.886602 | 2.9242 | 1.886672 | 2.9243 |
| vec8 | 2.580650 | 4.0000 | 2.581152 | 4.0008 |
| vec16 | 5.161295 | 8.0000 | 5.161502 | 8.0003 |
| vec18 | 5.806455 | 9.0000 | 5.806730 | 9.0004 |
