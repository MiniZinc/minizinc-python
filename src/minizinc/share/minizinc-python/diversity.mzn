/***
 @groupdef diversity MiniZinc definitions for the MiniZinc diversity extension.

 These annotations and predicates can be used to produce diverse set of
 solutions.In order to use them in a model, include the file "diversity.mzn".
*/


/***
 @groupdef diversity.annotations Annotations provided to guide the MiniZinc diversity extension.
*/

annotation diversity_incremental(int: k, float: gap);
annotation diversity_global(int: k, float: gap);
annotation diversity_pairwise(array[int] of var int: x, string: compare_fn);
annotation diversity_pairwise(array[int,int] of var int: x, string: compare_fn);
annotation diversity_pairwise(array[int] of var float: x, string: compare_fn);
annotation diversity_pairwise(array[int,int] of var float: x, string: compare_fn);
annotation diversity_aggregator(string);
annotation diversity_combinator(string);
annotation diversity_intra_constraint(string);
annotation diversity_inter_constraint(string);

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
  "hamming_distance: x and x must have identical index sets",
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
  "hamming_distance: x and x must have identical index sets",
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
  "manhattan_distance: x and x must have identical index sets",
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
  "manhattan_distance: x and x must have identical index sets",
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
  "manhattan_distance: x and x must have identical index sets",
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
  "manhattan_distance: x and x must have identical index sets",
  let {
    any: xx = array1d(x);
    any: yy = array1d(y);
  } in sum(i in index_set(xx)) (abs(xx[i] - yy[i]))
);
