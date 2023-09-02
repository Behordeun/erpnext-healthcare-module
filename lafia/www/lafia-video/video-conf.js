

const { connect, createLocalTracks } = Twilio.Video;


// const getToken = async (user=29, roomName="CR00001") => {
//   // call /users/access/generate to generate token
//   const url = "https://api.lafia.io" + "/users/access/generate";
  
//   const data = {
//       identity: user,
//       room: roomName
//   };
  
//   try {
//       const Token = await $.ajax({
//       url: url,
//           type: 'POST',
//           data: data
//       });
//       console.log(Token.data)
//       return Token.data;
//   } catch (e) {
//       console.dir(e);
//       alert("unable to connect, please refresh page!")
//   }
// }

const getToken = async () => {
  const loggedInUser = frappe.session.user;
  console.log(frappe.session.user);
  let token = "";
  const response = await fetch(
    "https://app.lafia.io/api/method/lafia.api.video-conf.video_conf.get_twilio_auth_token?" +
      new URLSearchParams({
        username: frappe.session.user,
        room: "CR00001"
      }),
    {
      method: "GET",
      mode: "same-origin",
    }
  );
  const data = await response.json();
  return data.message;
};

const toggleVideo = (room) => {
  const videoButton = document.querySelector(".video-control");
  videoButton.addEventListener("click", () => {
    room.localParticipant.videoTracks.forEach((publication) => {
      if (videoButton.dataset.switch === "on") {
        publication.track.disable();
        videoButton.dataset.switch = "off";
      } else {
        publication.track.enable();
        videoButton.dataset.switch = "on";
      }
    });
  });
};

const toggleAudio = (room) => {
  const audioButton = document.querySelector(".audio-control");
  audioButton.addEventListener("click", function () {
    room.localParticipant.audioTracks.forEach((publication) => {
      if (audioButton.dataset.switch === "on") {
        publication.track.disable();
        audioButton.dataset.switch = "off";
      } else {
        publication.track.enable();
        audioButton.dataset.switch = "on";
      }
    });
  });
}

const handleDisconnect = (room) => {
  const hangupButton = document.querySelector(".end-call");
  hangupButton.addEventListener("click", async () => {
    if (hangupButton.dataset.switch === "on") {
      hangupButton.textContent = "Call Again"
      hangupButton.dataset.switch = "off"
    // To disconnect from a Room
    room.disconnect();
    } else {
      const token = await getToken();
      hangupButton.dataset.switch = "on"
      hangupButton.textContent = "Hang Up"
      startVideo(token)
    }
  })
}

const startVideo = (token) => {
  createLocalTracks({
    audio: true,
    video: { width: 640 },
  }).then((localTracks) => {
    connect(token, {
      // logLevel: 'debug',
      tracks: localTracks,
    })
      .then((room) => {
        console.log(`Connected to Room: ${room.name}`);
        const localParticipant = room.localParticipant;
        localParticipant.tracks.forEach((publication) => {
          if (publication.track) {
            document
              .getElementById("my-media-div")
              .appendChild(publication.track.attach());
          }
        });

        toggleVideo(room);
        toggleAudio(room);
        handleDisconnect(room);
        
        console.log(localParticipant);
        console.log(
          `Connected to the Room as LocalParticipant "${localParticipant.identity}"`
        );
        room.participants.forEach((participant) => {
          console.log(
            `Participant "${participant.identity}" is connected to the Room`
          );
          console.log("participant");
          console.log(participant);
          participant.tracks.forEach((publication) => {
            if (publication.track) {
              document
                .getElementById("remote-media-div")
                .appendChild(publication.track.attach());
            }
          });

          participant.on("trackSubscribed", (track) => {
            document
              .getElementById("remote-media-div")
              .appendChild(track.attach());
          });
        });
        // Log new Participants as they connect to the Room
        room.once("participantConnected", (participant) => {
          console.log(
            `Participant "${participant.identity}" has connected to the Room`
          );
        });
        room.on("participantConnected", (participant) => {
          participant.tracks.forEach((publication) => {
            if (publication.isSubscribed) {
              const track = publication.track;
              document
                .getElementById("remote-media-div")
                .appendChild(track.attach());
            }
          });

          participant.on("trackSubscribed", (track) => {
            document
              .getElementById("remote-media-div")
              .appendChild(track.attach());
          });
          console.log(
            `A remote Participant connected: ${participant.identity}`
          );
        });
        // Log Participants as they disconnect from the Room
        room.on("participantDisconnected", (participant) => {
          console.log(
            `Participant "${participant.identity}" has disconnected from the Room`
          );
          // Detach the local media elements
          participant.tracks.forEach(publication => {
            const attachedElements = publication.track.detach();
            attachedElements.forEach(element => element.remove());
          });
        });
        room.on('disconnected', room => {
          // Detach the local media elements
          room.localParticipant.tracks.forEach(publication => {
            const attachedElements = publication.track.detach();
            attachedElements.forEach(element => element.remove());
          });
        });
      })
      .catch((error) => {
        console.error(`Unable to connect to room: ${error.message}`);
      });
  });
}

frappe.ready(() => {
  Promise.resolve(getToken()).then((token) => {
    createLocalTracks({
      audio: true,
      video: { width: 640 },
    }).then((localTracks) => {
      connect(token, {
        // logLevel: 'debug',
        tracks: localTracks,
      })
        .then((room) => {
          console.log(`Connected to Room: ${room.name}`);
          const localParticipant = room.localParticipant;
          localParticipant.tracks.forEach((publication) => {
            if (publication.track) {
              document
                .getElementById("my-media-div")
                .appendChild(publication.track.attach());
            }
          });

          toggleVideo(room);
          toggleAudio(room);
          handleDisconnect(room);
          
          console.log(localParticipant);
          console.log(
            `Connected to the Room as LocalParticipant "${localParticipant.identity}"`
          );
          room.participants.forEach((participant) => {
            console.log(
              `Participant "${participant.identity}" is connected to the Room`
            );
            console.log("participant");
            console.log(participant);
            participant.tracks.forEach((publication) => {
              if (publication.track) {
                document
                  .getElementById("remote-media-div")
                  .appendChild(publication.track.attach());
              }
            });

            participant.on("trackSubscribed", (track) => {
              document
                .getElementById("remote-media-div")
                .appendChild(track.attach());
            });
          });
          // Log new Participants as they connect to the Room
          room.once("participantConnected", (participant) => {
            console.log(
              `Participant "${participant.identity}" has connected to the Room`
            );
          });
          room.on("participantConnected", (participant) => {
            participant.tracks.forEach((publication) => {
              if (publication.isSubscribed) {
                const track = publication.track;
                document
                  .getElementById("remote-media-div")
                  .appendChild(track.attach());
              }
            });

            participant.on("trackSubscribed", (track) => {
              document
                .getElementById("remote-media-div")
                .appendChild(track.attach());
            });
            console.log(
              `A remote Participant connected: ${participant.identity}`
            );
          });
          // Log Participants as they disconnect from the Room
          room.on("participantDisconnected", (participant) => {
            console.log(
              `Participant "${participant.identity}" has disconnected from the Room`
            );
            // Detach the local media elements
            participant.tracks.forEach(publication => {
              const attachedElements = publication.track.detach();
              attachedElements.forEach(element => element.remove());
            });
          });
          room.on('disconnected', room => {
            // Detach the local media elements
            room.localParticipant.tracks.forEach(publication => {
              const attachedElements = publication.track.detach();
              attachedElements.forEach(element => element.remove());
            });
          });
        })
        .catch((error) => {
          console.error(`Unable to connect to room: ${error.message}`);
        });
    });
  });
});

// connect('eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiIsImN0eSI6InR3aWxpby1mcGE7dj0xIn0.eyJqdGkiOiJTS2Q3MDZlNWVhNzcyMmNmMWUxYzFhYzNhOGYzY2NkNGRmLTE2Mjc0ODc0MzgiLCJpc3MiOiJTS2Q3MDZlNWVhNzcyMmNmMWUxYzFhYzNhOGYzY2NkNGRmIiwic3ViIjoiQUNmZDA4Y2Q5YzA3YmM5YmU4NmI4ZmUxNmY5MjRmNDI5YiIsImV4cCI6MTYyNzQ5MTAzOCwiZ3JhbnRzIjp7ImlkZW50aXR5IjoidGVzdC11c2VyIiwidmlkZW8iOnsicm9vbSI6Imp1bmtpZSJ9fX0.QylZ9h1A41-f6mVIQVHkvHIxczYq3sOIISzJo6hdBPY', { name:'junkie' }).then(room => {
//   console.log(`Successfully joined a Room: ${room}`);
//   room.on('participantConnected', participant => {
//     console.log(`A remote Participant connected: ${participant}`);
//   });
// }, error => {
//   console.error(`Unable to connect to Room: ${error.message}`);
// });
