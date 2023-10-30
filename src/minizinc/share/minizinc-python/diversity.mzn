/***
 @groupdef diversity MiniZinc definitions for the MiniZinc diversity extension.

 These annotations and predicates can be used to produce diverse set of
 solutions.In order to use them in a model, include the file "diversity.mzn".
*/


/***
 @groupdef diversity.annotations Annotations provided to guide the MiniZinc diversity extension.
*/

/** @group diversity.annotations Produce at most \a k number of diverse solutions with thier objective values 
  bounded between optimal value and \a gap % from the optimal. Diverse solutions are obtained one after the other
  and distance to kth diverse solution is sum of pairwise distance to all the previous diverse solutions 
*/
annotation diversity_incremental(int: k, float: gap);
/** @group diversity.annotations
  Returns the Hamming distance between \a x and \a compare_fn
*/
annotation diverse_pairwise(array[int] of var int: x, string: compare_fn);
/** @group diversity.annotations
  Returns the Hamming distance between \a x and \a compare_fn
*/
annotation diverse_pairwise(array[$T] of var int: x, string: compare_fn) = diverse_pairwise(array1d(x), compare_fn);
/** @group diversity.annotations
  Returns the Hamming distance between \a x and \a compare_fn
*/
annotation diverse_pairwise(array[int] of var float: x, string: compare_fn);
/** @group diversity.annotations
  Returns the Hamming distance between \a x and \a compare_fn
*/
annotation diverse_pairwise(array[$T] of var float: x, string: compare_fn) = diverse_pairwise(array1d(x), compare_fn);

/***
 @groupdef diversity.distance Distance functions provided in the MiniZinc diversity extension.
*/

/** @group diversity.distance
  Returns the Hamming distance between \a x and \a y.
*/
function int: hamming_distance(
  array[$A] of opt $T: x,
  array[$A] of opt $T: y
) = assert(
  index_sets_agree(x, y),
  "hamming_distance: x and y must have identical index sets",
  let {
    any: xx = array1d(x);
    any: yy = array1d(y);
  } in count(i in index_set(array1d(xx))) (xx[i] != yy[i])
);

/** @group diversity.distance
  Returns the Hamming distance between \a x and \a y.
*/
function var int: hamming_distance(
  array[$A] of var opt $T: x,
  array[$A] of var opt $T: y
) = assert(
  index_sets_agree(x, y),
  "hamming_distance: x and y must have identical index sets",
  let {
    any: xx = array1d(x);
    any: yy = array1d(y);
  } in count(i in index_set(array1d(xx))) (xx[i] != yy[i])
);

/** @group diversity.distance
  Returns the Hamming distance between \a x and \a y.
*/
function int: manhattan_distance(
  array[$A] of $$T: x,
  array[$A] of $$T: y
) = assert(
  index_sets_agree(x, y),
  "manhattan_distance: x and y must have identical index sets",
  let {
    any: xx = array1d(x);
    any: yy = array1d(y);
  } in sum(i in index_set(xx)) (abs(xx[i] - yy[i]))
);

/** @group diversity.distance
  Returns the Hamming distance between \a x and \a y.
*/
function var int: manhattan_distance(
  array[$A] of var $$T: x,
  array[$A] of var $$T: y
) = assert(
  index_sets_agree(x, y),
  "manhattan_distance: x and y must have identical index sets",
  let {
    any: xx = array1d(x);
    any: yy = array1d(y);
  } in sum(i in index_set(xx)) (abs(xx[i] - yy[i]))
);

/** @group diversity.distance
  Returns the Hamming distance between \a x and \a y.
*/
function float: manhattan_distance(
  array[$A] of float: x,
  array[$A] of float: y
) = assert(
  index_sets_agree(x, y),
  "manhattan_distance: x and y must have identical index sets",
  let {
    any: xx = array1d(x);
    any: yy = array1d(y);
  } in sum(i in index_set(xx)) (abs(xx[i] - yy[i]))
);


/** @group diversity.distance
  Returns the Hamming distance between \a x and \a y.
*/
function var float: manhattan_distance(
  array[$A] of var float: x,
  array[$A] of var float: y
) = assert(
  index_sets_agree(x, y),
  "manhattan_distance: x and y must have identical index sets",
  let {
    any: xx = array1d(x);
    any: yy = array1d(y);
  } in sum(i in index_set(xx)) (abs(xx[i] - yy[i]))
);
