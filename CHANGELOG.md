# Not released, target: 1.0.0

 - Added Support for Scaled Extra bytes
 
 - Added more type hints, which in combination to others changes
   should help IDEs provide better autocompletion.
   
 - Added pylas.LazBackend to be able to select the backend to use if
   many are installed

 - Changed support for the laszip backend to now use
   bindings to the laszip c++ API instead of using
   the laszip executable found in the PATH

 - Changed simplify EVLR
    Previously we had a EVLR class which was just a VLR subclass.
    Now EVLR are just VLR, kepts in a different list, and written
    as EVLRs if there are any.

 - Changed: VLRList now subclass list
  
 - Changed Header classes & Vlr
    The hierarchy of header classes (RawHeader1_1, RawHeader1_2, etc)
    is removed and now only one class exists LasHeader, where most
    of the fields that reader/writers care about are removed and
    field that user care about are kept and put in user-friendly classes.

    The vlrs are now also a part of the header
    (it simplifies synchronizing, the header, vlrs, point_format and extra bytes vlr)
   
 - Removed pylas merge


# 0.5.0b
 
 - Added write ('r') and append ('a') mode to pylas.open
 - Added ability to read a LAS/LAZ file chunk by chunk
 - Added ability to write as LAS/LAZ chunk by chunk
 - Added ability to append points to LAS/LAZ (LAZ only with lazrs)

 - Added SubFieldView class to handle LAS fields which are bit fields
   (e.g. return_number) in a more consistent way than was done.

 - Removed lazperf support for compression/decompression
 

# 0.4.3

 - Added maximum version to the lazrs optional dependency to 0.2.0.

# 0.4.2

  - Fixed writing LAZ file with EVLR when piping through laszip.exe

# 0.4.0

  - Added support for compressing & decompressing with laz-rs (supports parallel processing)
  - Added support for compressing using laszip.exe
  - Added Overflow & Underflow checks to the scaled x, y,z setters

# 0.3.4
    
  - Allow adding extra bytes to all las versions
  - Added rounding of x, y z coordinates when they are set
    
# 0.3.2

  - Changed the x, y, z offsets are not longer changed when new x,y or
    are set
    
# 0.3.0

  - Added `supported_version` function which returns the LAS version
           supported by pylas
  - Added a new `PointFormat` class
  - Added a `merge_las` function
  - Added `mins` & `maxs` properties to the header, they
           provide access to the x, y, z mins and maxs as numpy arrays
     
  - Fixed initialize the `header.date` to `date.today()`

# 0.2.0

  - Updated lazperf to handle lazperf exrabytes 

  - Changed all pylas specific exception now inhereits the `PylasError`
    exception class

  - Fixed extra dimension bug where the extra field was added to
    the LasData attrbute but not the the points array


# 0.1.4
  
# 0.1.0
  
  - Initial version


