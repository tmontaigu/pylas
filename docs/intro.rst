============
Introduction
============

LAS is a public file format meant to exchange 3D point data, mostly used to exchange lidar point clouds.
LAZ is compression **lossless** format of the LAS format.

LAS files are organized in 3 main parts:

1) Header
2) VLRs
3) Point Records


The header contains information about the data such as its version, the point format (which tells the different
dimensions stored for each points).

After the header, LAS files may contains VLRs (Variable Length Record).
VLRs are meant to store additional information such as the SRS, description on extra dimensions added to the points.
VLRs are divided in two parts:

1) header
2) payload

The payload is limited to 65,535 bytes (Because in the header, the length of the payload is stored on a uint16).

The last chunk of data (and the biggest one) contains the point records. In a LAS file, points are stored sequentially.

Version 1.4 of the LAS specification added a last block following the point records: EVLRs (Extended Variable
Length Record) which are the same thing as VLRs but they can carry a higher payload (length of the payload is stored
on a uint64)
