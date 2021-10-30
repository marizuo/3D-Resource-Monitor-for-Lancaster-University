# 3D-Resource-Monitor-for-Lancaster-University
3D Resource Monitor for Lancaster University

This is a project carried out over the 2019/2020 academic year to process, visualise and analyse the large quantities of resource consumption data collected by Lancaster University.

The 3D tileset was created on a basis of a 2D OSM map and extruded using private university data using the FME program. The FME workspaces are attached but without data.

The raw data is processed into the standardized format ready for the dashboard using some Python scripts. The processing includes error detection, duplicate resolutions and filling missing data.

The dashboard itself is based on the Dash by Plotly library, and uses the additional visdcc library to run Javascript client side in order to create the 3D map using CesiumJS. 
This is a novel implementation as the time dynamic element is created in Dash and creates temporal 3D display in Cesium. This allows server side manipulation, filtering of the consumption data which would be unwieldy to do client-side, allowing building adminstrators and other staff to use it on lightweight devices (phones, tablets)

This project was deployed onto Google Cloud Platform.
