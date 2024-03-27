.. raw:: html

   <script>
   // JavaScript code here
   document.addEventListener("DOMContentLoaded", function() {
       var hash = window.location.hash;
       if (hash) {
           var anchor = hash.substring(1);
           window.location.href = "server-selection.md#" + anchor;
       } else {
           window.location.href = "server-selection.md";
       }
   });
   </script>
   