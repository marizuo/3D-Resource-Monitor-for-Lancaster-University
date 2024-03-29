# 3D-Resource-Monitor-for-Lancaster-University
3D Resource Monitor for Lancaster University

This is a project carried out over the 2019/2020 academic year to process, visualise and analyse the large quantities of resource consumption data collected by Lancaster University.

The 3D tileset was created on a basis of a 2D OSM map and extruded using private university data using the FME program. The FME workspaces are attached but without data.

The raw data is processed into the standardized format ready for the dashboard using some Python scripts. The processing includes error detection, duplicate resolutions and filling missing data.

The dashboard itself is based on the Dash by Plotly library, and uses the additional visdcc library to run Javascript client side in order to create the 3D map using CesiumJS. 
This is a novel implementation as the time dynamic element is created in Dash and creates temporal 3D display in Cesium. This allows server side manipulation, filtering of the consumption data which would be unwieldy to do client-side, allowing building adminstrators and other staff to use it on lightweight devices (phones, tablets)

This project was deployed onto Google Cloud Platform.


Dashboard sample:
<p align="center">
  <img src="https://user-images.githubusercontent.com/52913193/139739689-d8e45f2f-cadb-430d-88c0-72f89dcfbc15.png" />
</p>


Building Occupancy example: 3d, interactive:
<p align="center">
  <img src="https://user-images.githubusercontent.com/52913193/139739506-7c957cd3-df57-4a81-b711-72a9d3ac86b5.png" />
</p>



OSM campus map:
<p align="center">
  <img src="https://user-images.githubusercontent.com/52913193/139740394-741d2108-cd61-4cd3-8b60-c263e16aa05a.png" />
</p>


Matching via OSM:
<p align="center">
  <img src="https://user-images.githubusercontent.com/52913193/139739310-9bbfc5bc-641a-4143-afcc-8fcce7f2a532.png" />
</p>



FME data flow: 
<p align="center">
  <img src="https://user-images.githubusercontent.com/52913193/139739368-8debba86-f9ec-47d7-8e32-5c050c077cb8.png" />
</p>

<p align="center">
  <img src="https://user-images.githubusercontent.com/52913193/139739407-d99ea067-d72c-4d9a-a1f3-34188d57d62b.png" />
</p>

